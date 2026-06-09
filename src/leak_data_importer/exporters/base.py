"""Базовый класс и утилиты для экспортёров.

Все экспортёры должны быть безопасны по PII: по умолчанию применяют
маскирование/хэширование через redaction utilities и PiiSafeLogger.
"""

from __future__ import annotations

import json
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, List, Optional

from leak_data_importer.utils.logging import PiiSafeLogger
from leak_data_importer.utils.redaction import (
    redact_email,
    redact_inn,
    redact_passport,
    redact_phone,
    redact_snils,
)

logger = PiiSafeLogger(__name__)


def get_default_redactors() -> Dict[str, Callable[[str], str]]:
    """Возвращает стандартный набор редакторов для высокорисковых полей."""
    return {
        "passport": redact_passport,
        "snils": redact_snils,
        "inn": redact_inn,
        "phone": redact_phone,
        "email": redact_email,
    }


class BaseExporter(ABC):
    """Абстрактный базовый экспортёр.

    Дочерние классы реализуют export(result, output_path, **options).
    Обязательно используют редактирование PII и логирование через PiiSafeLogger.
    """

    name: str = "base"
    supported_formats: tuple[str, ...] = ()

    def __init__(self, redaction_level: str = "standard", **options: Any):
        self.redaction_level = redaction_level
        # Поддержка старого флага redact_pii=True/False для совместимости с существующими вызовами
        if "redact_pii" in options:
            self.redact_pii = bool(options.pop("redact_pii"))
            if self.redact_pii and redaction_level == "standard":
                pass
            elif not self.redact_pii:
                self.redaction_level = "none"
        else:
            self.redact_pii = redaction_level != "none"
        self.options = options
        self.redactors = get_default_redactors() if self.redaction_level != "none" else {}

    @abstractmethod
    def export(
        self,
        result: Any,
        output_path: Path | str,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """Выполняет экспорт.

        Args:
            result: ImportGraphResult или список записей/сущностей.
            output_path: директория или файл назначения.
        Returns:
            dict с метриками (кол-во записей, файлы и т.д.).
        """
        raise NotImplementedError

    def _apply_redaction(self, value: Any, field_hint: str = "") -> Any:
        """Применяет редактирование если есть подходящий редaktor."""
        if self.redaction_level == "none" or value is None:
            return value
        if not isinstance(value, str):
            return value
        hint = field_hint.lower()
        for key, redactor in self.redactors.items():
            if key in hint:
                try:
                    return redactor(value)
                except Exception:
                    logger.warning("Redaction failed for field %s, using masked value", key)
                    return "***"
        # Дополнительная эвристика по содержимому
        if "@" in value and "email" in self.redactors:
            return self.redactors["email"](value)
        digits = "".join(c for c in value if c.isdigit())
        if len(digits) in (10, 11) and "phone" in self.redactors:
            return self.redactors["phone"](value)
        if len(digits) == 10 and "inn" in self.redactors:
            return self.redactors["inn"](value)
        return value

    def _safe_write_json(self, path: Path, data: Any) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2, default=str)

    # --- Helpers expected by CSV/JSONLines exporters (added for completeness) ---

    def get_entities_and_relationships(self, result: Any) -> tuple[list[Any], list[Any]]:
        """Нормализует вход (ImportGraphResult, dict или сырой граф) в (entities, relationships)."""
        if result is None:
            return [], []
        # ImportGraphResult
        if hasattr(result, "graph"):
            g = result.graph
            ents = getattr(g, "entities", []) or []
            rels = getattr(g, "relationships", []) or []
            return list(ents), list(rels)
        # dict with 'graph'
        if isinstance(result, dict):
            g = result.get("graph") or result
            if isinstance(g, dict):
                return g.get("entities", []), g.get("relationships", [])
            return g.get("entities", []), g.get("relationships", [])
        # raw graph-like
        if hasattr(result, "entities") and hasattr(result, "relationships"):
            return list(result.entities), list(result.relationships)
        return [], []

    def _safe_serialize_entity(self, entity: Any) -> dict[str, Any]:
        """Сериализует сущность с применением редактирования PII."""
        if isinstance(entity, dict):
            d = dict(entity)
        else:
            d = {
                "id": getattr(entity, "id", None),
                "type": getattr(entity, "type", "unknown"),
                "canonical_key": getattr(entity, "canonical_key", None),
                "source_refs": getattr(entity, "source_refs", []),
            }
            props = getattr(entity, "properties", {}) or {}
            d.update({k: v for k, v in props.items() if not isinstance(v, (dict, list)) or k in ("raw_fields",)})
        # Применяем редактирование к строковым полям
        for k in list(d.keys()):
            if isinstance(d[k], str):
                d[k] = self._apply_redaction(d[k], k)
        # Массивы source_refs оставляем как строку
        if isinstance(d.get("source_refs"), (list, tuple)):
            d["source_refs"] = ",".join(str(x) for x in d["source_refs"])
        return d

    def _safe_serialize_relationship(self, rel: Any) -> dict[str, Any]:
        """Сериализует связь с редактированием."""
        if isinstance(rel, dict):
            d = {
                "from_id": rel.get("from_id"),
                "to_id": rel.get("to_id"),
                "type": rel.get("type"),
                "confidence": rel.get("confidence"),
            }
            props = rel.get("properties") or {}
            d.update({k: v for k, v in props.items() if not isinstance(v, (dict, list))})
        else:
            d = {
                "from_id": getattr(rel, "from_id", None),
                "to_id": getattr(rel, "to_id", None),
                "type": getattr(rel, "type", None),
                "confidence": getattr(rel, "confidence", None),
            }
            props = getattr(rel, "properties", {}) or {}
            d.update({k: v for k, v in props.items() if not isinstance(v, (dict, list))})
        # Редактирование
        for k in ("from_id", "to_id"):
            if isinstance(d.get(k), str):
                d[k] = self._apply_redaction(d[k], k)
        return d


# Константы, ожидаемые тестами экспортёров (PII поля для маскирования/аудита)
PII_SENSITIVE_FIELDS = ("passport", "snils", "inn", "foreign_passport", "phone", "email")

__all__ = ["BaseExporter", "get_default_redactors", "PII_SENSITIVE_FIELDS"]
