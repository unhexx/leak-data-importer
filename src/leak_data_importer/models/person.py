"""Normalized person record extracted from leak data."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Optional


@dataclass(slots=True)
class PersonRecord:
    """Normalized record for a person from leaked data.

    Designed to be robust against the messy hybrid report formats
    commonly found in Russian breach dumps (report_*.txt style).
    """

    full_name: Optional[str] = None
    birth_date: Optional[date] = None

    # Core normalized identifiers (deduplicated)
    phones: list[str] = field(default_factory=list)
    emails: list[str] = field(default_factory=list)
    passports: list[str] = field(default_factory=list)
    snils: list[str] = field(default_factory=list)
    inn: list[str] = field(default_factory=list)

    # Additional fields frequently seen in these dumps
    esia_id: Optional[str] = None
    addresses: list[str] = field(default_factory=list)
    registration_dates: list[str] = field(default_factory=list)
    other_ids: dict[str, list[str]] = field(default_factory=dict)  # ICCID, IMSI, VIN, etc.

    # Provenance & quality
    source_file: Optional[str] = None
    source_block_id: Optional[str] = None
    confidence: Optional[float] = None          # aggregated from (NN/NN) or (xNN) markers
    parsing_strategy: Optional[str] = None      # which strategy extracted this record

    # Full original messy data for audit / reprocessing
    raw_data: dict[str, list[str]] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            k: v for k, v in self.__dict__.items()
            if not k.startswith("_")
        }
