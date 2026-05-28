"""Normalized person record extracted from leak data."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Optional


@dataclass(slots=True)
class PersonRecord:
    """Normalized record for a person from leaked data.

    All identifiers are stored in normalized form where possible.
    Source-specific raw values are kept in raw_data for traceability.
    """

    full_name: Optional[str] = None
    birth_date: Optional[date] = None

    # Normalized identifiers
    phones: list[str] = field(default_factory=list)          # E.164 format when possible
    emails: list[str] = field(default_factory=list)
    passports: list[str] = field(default_factory=list)       # Russian internal passport
    snils: list[str] = field(default_factory=list)           # Normalized SNILS
    inn: list[str] = field(default_factory=list)             # INN (tax ID)

    # Metadata
    source_file: Optional[str] = None
    source_block_id: Optional[str] = None
    confidence: Optional[float] = None                       # 0.0 - 1.0 aggregated

    # Keep original messy values for auditing / re-processing
    raw_data: dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict:
        d = {k: v for k, v in self.__dict__.items() if k != "raw_data"}
        d["raw_data"] = self.raw_data
        return d
