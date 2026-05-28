"""
ImportGraphResult - the main output container when parsing leak data for link analysis.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from leak_data_importer.graph.entity import Entity, ImportGraph, Relationship


@dataclass(slots=True)
class ImportGraphResult:
    """
    Rich output of an importer when running in graph mode.

    Contains both the normalized graph (entities + relationships) and
    the original flat records for backward compatibility.
    """
    graph: ImportGraph = field(default_factory=ImportGraph)
    flat_records: list[dict] = field(default_factory=list)   # original PersonRecord style
    stats: dict[str, Any] = field(default_factory=dict)

    def summary(self) -> dict:
        return {
            "entities_total": len(self.graph.entities),
            "entities_by_type": self.graph.entity_count_by_type(),
            "relationships_total": len(self.graph.relationships),
            "flat_records": len(self.flat_records),
            "stats": self.stats,
        }
