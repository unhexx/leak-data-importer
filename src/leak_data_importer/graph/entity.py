"""
Entity and Relationship models for building a linkable graph from leak data.

This module defines the core data model for "object + connections" analysis,
which is the next layer after raw record parsing.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional
from uuid import uuid4


@dataclass(slots=True)
class Entity:
    """
    Generic entity representing one real-world object found in leak data.

    Examples of types:
        - "person"
        - "phone_number"
        - "email_address"
        - "passport"
        - "snils"
        - "esia_account"
        - "physical_address"
        - "vehicle"
        - "sim_card"
        - "ip_address"
    """
    id: str = field(default_factory=lambda: str(uuid4()))
    type: str = "unknown"
    properties: dict[str, Any] = field(default_factory=dict)
    source_refs: list[str] = field(default_factory=list)   # which original blocks/files this came from

    # Optional normalized key for deduplication (e.g. normalized phone, email lower, passport number)
    canonical_key: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "type": self.type,
            "properties": self.properties,
            "source_refs": self.source_refs,
            "canonical_key": self.canonical_key,
        }


@dataclass(slots=True)
class Relationship:
    """
    A directed or undirected link between two entities.

    Common types used in leak data:
        - "has_phone"
        - "has_email"
        - "has_document"
        - "owns_account"
        - "registered_at"
        - "used_from_ip"
        - "associated_with"
    """
    from_id: str
    to_id: str
    type: str
    properties: dict[str, Any] = field(default_factory=dict)
    source_ref: Optional[str] = None
    confidence: Optional[float] = None

    def to_dict(self) -> dict:
        return {
            "from_id": self.from_id,
            "to_id": self.to_id,
            "type": self.type,
            "properties": self.properties,
            "source_ref": self.source_ref,
            "confidence": self.confidence,
        }


@dataclass(slots=True)
class ImportGraph:
    """Container for all entities and relationships extracted from one or more files."""
    entities: list[Entity] = field(default_factory=list)
    relationships: list[Relationship] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "entities": [e.to_dict() for e in self.entities],
            "relationships": [r.to_dict() for r in self.relationships],
            "metadata": self.metadata,
        }

    def entity_count_by_type(self) -> dict[str, int]:
        counts: dict[str, int] = {}
        for e in self.entities:
            counts[e.type] = counts.get(e.type, 0) + 1
        return counts
