"""
Базовый класс и общие утилиты для всех экспортёров.

Предоставляет единый интерфейс, поддержку безопасной обработки PII
и вспомогательные методы сериализации сущностей и связей.

Все экспортёры (CSV, JSON Lines, Neo4j) должны наследоваться от BaseExporter
или использовать предоставляемые здесь хелперы.
"""

from __future__ import annotations

import json
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Iterable, Optional

from leak_data_importer.graph.entity import Entity, Relationship
from leak_data_importer.graph.result import ImportGraphResult
from leak_data_importer.utils.redaction import (
    is_pii_safe,
    redact_document,
    redact_email,
    redact_inn,
    redact_passport,
    redact_phone,
    redact_snils,
)


# Поля, которые считаются высокорисковыми PII по типу сущности
PII_SENSITIVE_FIELDS: dict[str, list[str]] = {
    "person": ["full_name", "birth_date"],  # ФИО и дата рождения — средний риск
    "passport": ["number"],
    "snils": ["number"],
    "inn": ["number"],
    "phone_number": ["number"],
    "email_address": ["address"],
    "physical_address": ["address"],
}


class BaseExporter(ABC):
    """
    Абстрактный базовый класс для экспортёров результатов импорта.

    Определяет общий контракт:
    - экспорт полного ImportGraphResult
    - поддержка опций (редакция PII, фильтрация типов сущностей)
    - безопасная сериализация с учётом PII

    Все конкретные экспортёры должны реализовывать метод export().
    """

    def __init__(self, redact_pii: bool = True, entity_types: Optional[list[str]] = None):
        """
        Args:
            redact_pii: Если True — чувствительные поля маскируются.
            entity_types: Если задан — экспортировать только указанные типы сущностей.
        """
        self.redact_pii = redact_pii
        self.entity_types = set(entity_types) if entity_types else None

    @abstractmethod
    def export(
        self,
        result: ImportGraphResult,
        output_path: str | Path,
        **options: Any,
    ) -> dict[str, Any]:
        """
        Выполняет экспорт результата.

        Args:
            result: ImportGraphResult с сущностями и связями.
            output_path: Путь к файлу или директории (зависит от экспортёра).
            **options: Дополнительные параметры конкретного экспортёра.

        Returns:
            Словарь с метриками экспорта (кол-во записей, файлы и т.д.).
        """
        raise NotImplementedError

    def _should_include_entity(self, entity: Entity) -> bool:
        """Проверяет, нужно ли включать сущность в экспорт по фильтру типов."""
        if self.entity_types is None:
            return True
        return entity.type in self.entity_types

    def _safe_serialize_entity(self, entity: Entity) -> dict[str, Any]:
        """
        Возвращает безопасную для экспорта копию сущности.

        При redact_pii=True маскирует известные чувствительные поля.
        Сложные значения (списки/словари) сериализуются в JSON.
        """
        props = dict(entity.properties)

        if self.redact_pii:
            props = self._apply_redaction(entity.type, props)

        # Сериализуем сложные значения
        for key, value in list(props.items()):
            if isinstance(value, (dict, list)):
                props[key] = json.dumps(value, ensure_ascii=False)
            elif value is None:
                props[key] = ""

        return {
            "id": entity.id,
            "type": entity.type,
            "canonical_key": entity.canonical_key or "",
            "source_refs": "|".join(entity.source_refs) if entity.source_refs else "",
            **props,
        }

    def _apply_redaction(self, entity_type: str, props: dict[str, Any]) -> dict[str, Any]:
        """Применяет маскирование к чувствительным полям."""
        result = dict(props)
        sensitive_fields = PII_SENSITIVE_FIELDS.get(entity_type, [])

        for field in sensitive_fields:
            if field not in result or not result[field]:
                continue

            value = str(result[field])

            # Специфичные редаторы по типу сущности
            if entity_type == "passport":
                result[field] = redact_passport(value)
            elif entity_type == "snils":
                result[field] = redact_snils(value)
            elif entity_type == "inn":
                result[field] = redact_inn(value)
            elif entity_type == "phone_number":
                result[field] = redact_phone(value)
            elif entity_type == "email_address":
                result[field] = redact_email(value)
            elif entity_type == "physical_address":
                result[field] = redact_document(value)
            else:
                # Для person и остальных — мягкая маскировка
                if len(value) > 4:
                    result[field] = value[:2] + "**" + value[-2:]

        return result

    def _safe_serialize_relationship(self, rel: Relationship) -> dict[str, Any]:
        """Безопасная сериализация связи (связи обычно не содержат PII напрямую)."""
        props = dict(rel.properties)
        for key, value in list(props.items()):
            if isinstance(value, (dict, list)):
                props[key] = json.dumps(value, ensure_ascii=False)

        return {
            "from_id": rel.from_id,
            "to_id": rel.to_id,
            "type": rel.type,
            "confidence": rel.confidence if rel.confidence is not None else "",
            "source_ref": rel.source_ref or "",
            **props,
        }

    def filter_entities(self, entities: Iterable[Entity]) -> list[Entity]:
        """Фильтрует сущности согласно настройкам экспортёра."""
        return [e for e in entities if self._should_include_entity(e)]

    def get_entities_and_relationships(
        self, result: ImportGraphResult
    ) -> tuple[list[Entity], list[Relationship]]:
        """Возвращает отфильтрованные сущности и все связи."""
        entities = self.filter_entities(result.graph.entities)
        # Связи оставляем полностью — они важны для восстановления графа
        return entities, result.graph.relationships


def get_default_redactors() -> dict[str, Any]:
    """Возвращает словарь доступных функций редокции (для справки и тестов)."""
    return {
        "passport": redact_passport,
        "snils": redact_snils,
        "inn": redact_inn,
        "phone": redact_phone,
        "email": redact_email,
        "document": redact_document,
    }
