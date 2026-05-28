"""
Exact Pydantic v2 models as per the detailed specification.

These models represent the canonical output of the DossierParser.
"""

from pydantic import BaseModel, Field
from datetime import date, datetime
from typing import Optional, List, Dict, Any
from uuid import UUID, uuid4


class ParsedPerson(BaseModel):
    """Core normalized person extracted from the report."""
    fio: str
    birth_date: Optional[date] = None
    passports: List[str] = Field(default_factory=list)
    snils: Optional[str] = None
    inn: Optional[str] = None
    phones: List[str] = Field(default_factory=list)
    emails: List[str] = Field(default_factory=list)

    # From "ВСЕ НАЙДЕННЫЕ ЗНАЧЕНИЯ" section
    extra_phones: List[str] = Field(default_factory=list)
    extra_emails: List[str] = Field(default_factory=list)
    extra_passports: List[str] = Field(default_factory=list)
    extra_inns: List[str] = Field(default_factory=list)

    # Vehicles (if present in the report)
    vehicles: List[Dict[str, Any]] = Field(default_factory=list)

    # Main (most frequent / primary) identifiers — filled during post-processing
    main_phone: Optional[str] = None
    main_email: Optional[str] = None
    main_passport: Optional[str] = None
    main_inn: Optional[str] = None

    # Any additional structured data
    extra: Dict[str, Any] = Field(default_factory=dict)


class ParsedReport(BaseModel):
    """Complete structured output of parsing one report file."""

    report_id: UUID = Field(default_factory=uuid4)
    filename: str
    report_date: Optional[datetime] = None
    sources_count: int
    records_count: int

    # Main subject of the report
    main_person: ParsedPerson

    # Structured sections
    profile_section: Dict[str, Any] = Field(default_factory=dict)      # ПРОФИЛЬ + БАНКИ
    documents: List[Dict[str, Any]] = Field(default_factory=list)      # ДОКУМЕНТЫ
    addresses: List[Dict[str, Any]] = Field(default_factory=list)      # АДРЕСА
    employments: List[Dict[str, Any]] = Field(default_factory=list)    # МЕСТО РАБОТЫ
    connections: List[Dict[str, Any]] = Field(default_factory=list)    # ВОЗМОЖНЫЕ СВЯЗИ
    border_events: List[Dict[str, Any]] = Field(default_factory=list)  # ПЕРЕСЕЧЕНИЯ ГРАНИЦЫ
    websites: List[str] = Field(default_factory=list)                  # САЙТЫ...
    source_findings: List[Dict[str, Any]] = Field(default_factory=list)  # ИСТОЧНИКИ (raw + parsed)

    # Diagnostics
    warnings: List[str] = Field(default_factory=list)
    parsed_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = {
        "json_encoders": {
            datetime: lambda v: v.isoformat(),
            date: lambda v: v.isoformat(),
            UUID: lambda v: str(v),
        }
    }
