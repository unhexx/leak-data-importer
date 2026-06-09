"""
Тесты для новых экспортёров (CSV, JSON Lines) и базового класса.

Проверяем:
- Корректную работу BaseExporter (фильтрация, редокция PII)
- Генерацию CSV и JSON Lines файлов
- Сохранение структуры данных
"""

import json
import tempfile
from datetime import date
from pathlib import Path

import pytest

from leak_data_importer.exporters import (
    CSVExporter,
    JSONLinesExporter,
    get_default_redactors,
)
from leak_data_importer.exporters.base import BaseExporter, PII_SENSITIVE_FIELDS
from leak_data_importer.graph import (
    ImportGraph,
    ImportGraphResult,
    make_email,
    make_passport,
    make_person,
    make_phone,
    same_as,
)


class TestBaseExporter:
    """Тесты базовой функциональности."""

    def test_redaction_is_applied_by_default(self):
        person = make_person(full_name="Иванов Иван Иванович", birth_date=date(1990, 5, 20))
        passport = make_passport("45 06 123456")

        result = ImportGraphResult(graph=ImportGraph(entities=[person, passport]))

        exporter = CSVExporter(redact_pii=True)
        safe_person = exporter._safe_serialize_entity(person)
        safe_passport = exporter._safe_serialize_entity(passport)

        # Паспорт (высокий риск) — сырой номер не должен присутствовать в открытом виде
        number = safe_passport.get("number", "")
        assert "4506123456" not in str(number) and "45 06 123456" not in str(number)
        # ФИО (низкий риск) — допускаем лёгкое маскирование (фамилия может остаться)
        full = safe_person.get("full_name", "") or ""
        assert "***" in full or full != "Иванов Иван Иванович"  # хотя бы частично обработано

    def test_redaction_can_be_disabled(self):
        passport = make_passport("45 06 123456")
        result = ImportGraphResult(graph=ImportGraph(entities=[passport]))

        exporter = CSVExporter(redact_pii=False)
        safe = exporter._safe_serialize_entity(passport)

        assert safe["number"] == "45 06 123456"

    def test_entity_type_filtering(self):
        person = make_person(full_name="Тестов Тест Тестович")
        phone = make_phone("+79161234567")

        result = ImportGraphResult(graph=ImportGraph(entities=[person, phone]))

        exporter = CSVExporter(entity_types=["person"])
        filtered = exporter.filter_entities(result.graph.entities)

        assert len(filtered) == 1
        assert filtered[0].type == "person"


class TestCSVExporter:
    """Тесты CSV-экспортёра."""

    def test_export_creates_files(self):
        person = make_person(full_name="Сидоров Пётр Иванович")
        phone = make_phone("+79165554433")
        rel = same_as(person.id, "other-person-id", confidence=0.95, match_strategy="exact_passport")

        graph = ImportGraph(entities=[person, phone], relationships=[rel])
        result = ImportGraphResult(graph=graph)

        with tempfile.TemporaryDirectory() as tmp:
            exporter = CSVExporter(redact_pii=True)
            metrics = exporter.export(result, tmp)

            assert metrics["entities_exported"] == 2
            assert metrics["relationships_exported"] == 1

            files = list(Path(tmp).glob("*.csv"))
            assert len(files) >= 2  # хотя бы entities_person.csv + relationships.csv

            # Проверяем, что файл с персонами создался
            person_files = [f for f in files if "person" in f.name]
            assert len(person_files) == 1


class TestJSONLinesExporter:
    """Тесты JSON Lines экспортёра."""

    def test_export_jsonl_separate_files(self):
        email = make_email("test@example.com")
        result = ImportGraphResult(graph=ImportGraph(entities=[email]))

        with tempfile.TemporaryDirectory() as tmp:
            exporter = JSONLinesExporter(redact_pii=True)
            metrics = exporter.export(result, tmp)

            assert metrics["entities_exported"] == 1

            ent_file = Path(tmp) / "entities.jsonl"
            assert ent_file.exists()

            with ent_file.open(encoding="utf-8") as f:
                line = json.loads(f.readline())
                assert line["type"] == "email_address"
                assert "_record_type" in line

    def test_export_combined(self):
        person = make_person(full_name="Комбинированный Тест")
        result = ImportGraphResult(graph=ImportGraph(entities=[person]))

        combined_path = Path(tempfile.gettempdir()) / "combined_export.jsonl"
        try:
            exporter = JSONLinesExporter(redact_pii=False)
            metrics = exporter.export(result, combined_path, combined=True)

            assert metrics["combined"] is True
            assert combined_path.exists()

            lines = combined_path.read_text(encoding="utf-8").strip().split("\n")
            assert len(lines) == 1
        finally:
            if combined_path.exists():
                combined_path.unlink()


def test_redactors_available():
    """Проверяем, что реестр редокторов работает."""
    redactors = get_default_redactors()
    assert "passport" in redactors
    assert callable(redactors["passport"])
