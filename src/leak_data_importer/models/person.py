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

    # Additional fields frequently seen in rich blocks
    esia_id: Optional[str] = None
    translit_name: Optional[str] = None          # ФИО на латинице

    # Structured rich data (much better than dumping everything to raw_data)
    addresses: list[dict] = field(default_factory=list)           # [{"type": "registration", "value": "...", "date": "..."}]
    registration_events: list[dict] = field(default_factory=list) # date, ip, system, airport_code, etc.
    other_ids: dict[str, list[str]] = field(default_factory=dict) # inn, foreign_passport, ogrn, iccid, imsi, vin, etc.
    vehicle_info: dict = field(default_factory=dict)              # vin, model, year, etc.

    # Provenance & quality
    source_file: Optional[str] = None
    source_block_id: Optional[str] = None
    confidence: Optional[float] = None          # aggregated from (NN/NN) or (xNN) markers
    parsing_strategy: Optional[str] = None      # which strategy extracted this record

    # Full original messy data for audit / reprocessing
    raw_data: dict[str, list[str]] = field(default_factory=dict)

    def to_dict(self) -> dict:
        from dataclasses import asdict
        return asdict(self)
