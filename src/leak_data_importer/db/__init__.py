"""Database mapping and schema utilities for leak data reports."""

from leak_data_importer.db.models import (
    Address,
    AddressType,
    Base,
    ConnectionType,
    Document,
    DocType,
    Employment,
    Event,
    EventType,
    Person,
    PersonConnection,
    Report,
    SourceFinding,
    Vehicle,
)
from leak_data_importer.db.report_mapper import ReportMapper
from leak_data_importer.db.repositories import (
    BaseRepository,
    DocumentRepository,
    PersonRepository,
    ReportRepository,
)

__all__ = [
    "ReportMapper",
    # SQLAlchemy 2.0 models
    "Base",
    "Report",
    "Person",
    "Document",
    "Address",
    "Employment",
    "PersonConnection",
    "Vehicle",
    "Event",
    "SourceFinding",
    # Enum types
    "DocType",
    "AddressType",
    "ConnectionType",
    "EventType",
    # Repositories
    "BaseRepository",
    "ReportRepository",
    "PersonRepository",
    "DocumentRepository",
]
