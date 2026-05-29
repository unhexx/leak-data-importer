"""
SQLAlchemy 2.0 models for the leak data importer database.

Matches the schema defined in db/schema.sql.
Uses PostgreSQL enum types mapped to SQLAlchemy enums.
"""

from __future__ import annotations

from datetime import date, datetime
from enum import Enum as PyEnum
from typing import Any, Optional

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    Date,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    TIMESTAMP,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import DeclarativeBase, Relationship, relationship


# Use JSON for SQLite compatibility, JSONB for PostgreSQL
# The type_annotation_map will be configured in __init_args__ based on dialect


class Base(DeclarativeBase):
    """Declarative Base for all models."""

    type_annotation_map = {
        dict: JSON,  # Use JSON for cross-dialect compatibility
        datetime: TIMESTAMP(timezone=True),
    }


# =============================================
# ENUM TYPES (mapped to PostgreSQL enums)
# =============================================


class DocType(PyEnum):
    """Document type enum matching PostgreSQL doc_type."""

    PASSPORT_RF = "passport_rf"
    FOREIGN_PASSPORT = "foreign_passport"
    SNILS = "snils"
    INN = "inn"
    OMS_POLICY = "oms_policy"
    DRIVER_LICENSE = "driver_license"
    OTHER = "other"


class AddressType(PyEnum):
    """Address type enum matching PostgreSQL address_type."""

    REGISTRATION = "registration"
    ACTUAL = "actual"
    WORK = "work"
    PREVIOUS = "previous"
    BIRTH_PLACE = "birth_place"
    OTHER = "other"


class ConnectionType(PyEnum):
    """Connection type enum matching PostgreSQL connection_type."""

    PARENT = "parent"
    CHILD = "child"
    SPOUSE = "spouse"
    RELATIVE = "relative"
    TRAVEL_COMPANION = "travel_companion"
    FLIGHT_COMPANION = "flight_companion"
    ADDRESS_COHABITANT = "address_cohabitant"
    OTHER = "other"


class EventType(PyEnum):
    """Event type enum matching PostgreSQL event_type."""

    BORDER_CROSSING_IN = "border_crossing_in"
    BORDER_CROSSING_OUT = "border_crossing_out"
    FLIGHT = "flight"
    DTP = "dtp"
    FSSP_DEBT = "fssp_debt"
    OTHER = "other"


# =============================================
# CORE TABLE MODELS
# =============================================


class Report(Base):
    """
    Reports table - main entry point for imported reports.
    """

    __tablename__ = "reports"

    id = Column(UUID(as_uuid=True), primary_key=True, default=func.uuid_generate_v4())
    filename = Column(Text, nullable=False, unique=True)
    imported_at = Column(TIMESTAMP(timezone=True), nullable=False, default=func.now())
    report_date = Column(DateTime(timezone=True))
    sources_count = Column(Integer)
    records_count = Column(Integer)
    main_fio = Column(Text, nullable=False)
    main_birth_date = Column(Date)
    raw_header = Column(JSON)
    status = Column(Text, default="imported")
    warnings = Column(JSON, default=lambda: [])
    created_by = Column(Text)

    # Relationships
    persons = relationship("Person", back_populates="report", cascade="all, delete-orphan")
    documents = relationship("Document", back_populates="report", cascade="all, delete-orphan")
    addresses = relationship("Address", back_populates="report", cascade="all, delete-orphan")
    employments = relationship("Employment", back_populates="report", cascade="all, delete-orphan")
    person_connections = relationship("PersonConnection", back_populates="report", cascade="all, delete-orphan")
    vehicles = relationship("Vehicle", back_populates="report", cascade="all, delete-orphan")
    events = relationship("Event", back_populates="report", cascade="all, delete-orphan")
    source_findings = relationship("SourceFinding", back_populates="report", cascade="all, delete-orphan")


class Person(Base):
    """
    Persons table - main person records linked to reports.
    """

    __tablename__ = "persons"

    id = Column(UUID(as_uuid=True), primary_key=True, default=func.uuid_generate_v4())
    report_id = Column(UUID(as_uuid=True), ForeignKey("reports.id", ondelete="CASCADE"), nullable=False)
    fio = Column(Text, nullable=False)
    birth_date = Column(Date)
    main_passport = Column(Text)
    main_snils = Column(Text)
    main_inn = Column(Text)
    main_phone = Column(Text)
    main_email = Column(Text)
    passport_count = Column(Integer, default=0)
    phone_count = Column(Integer, default=0)
    email_count = Column(Integer, default=0)
    address_count = Column(Integer, default=0)
    extra_data = Column(JSONB, default=lambda: {})
    created_at = Column(TIMESTAMP(timezone=True), default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), default=func.now(), onupdate=func.now())

    # Relationships
    report = relationship("Report", back_populates="persons")
    documents = relationship("Document", back_populates="person", cascade="all, delete-orphan")
    addresses = relationship("Address", back_populates="person", cascade="all, delete-orphan")
    employments = relationship("Employment", back_populates="person", cascade="all, delete-orphan")
    person_connections = relationship("PersonConnection", back_populates="person", cascade="all, delete-orphan")
    vehicles = relationship("Vehicle", back_populates="person", cascade="all, delete-orphan")
    events = relationship("Event", back_populates="person", cascade="all, delete-orphan")
    source_findings = relationship("SourceFinding", back_populates="person", cascade="all, delete-orphan")

    # Indexes
    __table_args__ = (
        Index("idx_persons_fio_gin", "fio", postgresql_using="gin", postgresql_ops={"fio": "gin_trgm_ops"}),
        Index("idx_persons_main_passport", "main_passport"),
        Index("idx_persons_main_snils", "main_snils"),
        Index("idx_persons_main_inn", "main_inn"),
        Index("idx_persons_main_phone", "main_phone"),
    )


class Document(Base):
    """
    Documents table - passport, SNILS, INN, etc.
    """

    __tablename__ = "documents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=func.uuid_generate_v4())
    person_id = Column(UUID(as_uuid=True), ForeignKey("persons.id", ondelete="CASCADE"), nullable=False)
    report_id = Column(UUID(as_uuid=True), ForeignKey("reports.id", ondelete="CASCADE"), nullable=False)
    doc_type = Column(Enum(DocType), nullable=False)
    number = Column(Text, nullable=False)
    series = Column(Text)
    issue_date = Column(Date)
    expiry_date = Column(Date)
    issuer = Column(Text)
    issuer_code = Column(Text)
    status = Column(Text)
    birth_place = Column(Text)
    registration_address = Column(Text)
    extra = Column(JSONB, default=lambda: {})
    source_section = Column(Text)
    created_at = Column(TIMESTAMP(timezone=True), default=func.now())

    # Relationships
    person = relationship("Person", back_populates="documents")
    report = relationship("Report", back_populates="documents")

    # Indexes and constraints
    __table_args__ = (
        Index("idx_documents_person", "person_id"),
        Index("idx_documents_number", "number"),
        Index("idx_documents_type", "doc_type"),
        UniqueConstraint("person_id", "doc_type", "number", "report_id", name="uq_doc_per_report"),
    )


class Address(Base):
    """
    Addresses table - registration, actual, work addresses.
    """

    __tablename__ = "addresses"

    id = Column(UUID(as_uuid=True), primary_key=True, default=func.uuid_generate_v4())
    person_id = Column(UUID(as_uuid=True), ForeignKey("persons.id", ondelete="CASCADE"), nullable=False)
    report_id = Column(UUID(as_uuid=True), ForeignKey("reports.id", ondelete="CASCADE"), nullable=False)
    address_type = Column(Enum(AddressType), nullable=False)
    full_text = Column(Text, nullable=False)
    normalized = Column(JSONB)
    frequency = Column(Integer, default=1)
    source = Column(Text)
    extra = Column(JSONB, default=lambda: {})
    created_at = Column(TIMESTAMP(timezone=True), default=func.now())

    # Relationships
    person = relationship("Person", back_populates="addresses")
    report = relationship("Report", back_populates="addresses")

    # Indexes
    __table_args__ = (
        Index("idx_addresses_person", "person_id"),
        Index("idx_addresses_full_text_gin", "full_text", postgresql_using="gin", postgresql_ops={"full_text": "gin_trgm_ops"}),
    )


class Employment(Base):
    """
    Employments table - work history.
    """

    __tablename__ = "employments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=func.uuid_generate_v4())
    person_id = Column(UUID(as_uuid=True), ForeignKey("persons.id", ondelete="CASCADE"), nullable=False)
    report_id = Column(UUID(as_uuid=True), ForeignKey("reports.id", ondelete="CASCADE"), nullable=False)
    employer_name = Column(Text)
    employer_inn = Column(Text)
    employer_ogrn = Column(Text)
    position = Column(Text)
    start_date = Column(Date)
    end_date = Column(Date)
    salary_annual = Column(Numeric(15, 2))
    salary_monthly = Column(Numeric(15, 2))
    source = Column(Text)
    extra = Column(JSONB, default=lambda: {})
    created_at = Column(TIMESTAMP(timezone=True), default=func.now())

    # Relationships
    person = relationship("Person", back_populates="employments")
    report = relationship("Report", back_populates="employments")


class PersonConnection(Base):
    """
    PersonConnections table - relationships between persons (family, travel companions, etc.).
    """

    __tablename__ = "person_connections"

    id = Column(UUID(as_uuid=True), primary_key=True, default=func.uuid_generate_v4())
    person_id = Column(UUID(as_uuid=True), ForeignKey("persons.id", ondelete="CASCADE"), nullable=False)
    report_id = Column(UUID(as_uuid=True), ForeignKey("reports.id", ondelete="CASCADE"), nullable=False)
    related_fio = Column(Text, nullable=False)
    related_birth_date = Column(Date)
    connection_type = Column(Enum(ConnectionType), nullable=False)
    source = Column(Text)
    context = Column(JSONB)
    confidence = Column(Float, default=0.8)  # Using Float to match PostgreSQL REAL
    created_at = Column(TIMESTAMP(timezone=True), default=func.now())

    # Relationships
    person = relationship("Person", back_populates="person_connections")
    report = relationship("Report", back_populates="person_connections")


class Vehicle(Base):
    """
    Vehicles table - owned vehicles.
    """

    __tablename__ = "vehicles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=func.uuid_generate_v4())
    person_id = Column(UUID(as_uuid=True), ForeignKey("persons.id", ondelete="CASCADE"), nullable=False)
    report_id = Column(UUID(as_uuid=True), ForeignKey("reports.id", ondelete="CASCADE"), nullable=False)
    gos_number = Column(Text)
    vin = Column(Text)
    make_model = Column(Text)
    year = Column(Integer)
    extra = Column(JSONB, default=lambda: {})
    created_at = Column(TIMESTAMP(timezone=True), default=func.now())

    # Relationships
    person = relationship("Person", back_populates="vehicles")
    report = relationship("Report", back_populates="vehicles")


class Event(Base):
    """
    Events table - border crossings, flights, DTP, FSSP debts.
    """

    __tablename__ = "events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=func.uuid_generate_v4())
    person_id = Column(UUID(as_uuid=True), ForeignKey("persons.id", ondelete="CASCADE"), nullable=False)
    report_id = Column(UUID(as_uuid=True), ForeignKey("reports.id", ondelete="CASCADE"), nullable=False)
    event_type = Column(Enum(EventType), nullable=False)
    event_date = Column(TIMESTAMP(timezone=True))
    flight_number = Column(Text)
    airline = Column(Text)
    departure = Column(Text)
    arrival = Column(Text)
    country = Column(Text)
    direction = Column(Text)
    passport_used = Column(Text)
    companion_fio = Column(Text)
    debt_amount = Column(Numeric(15, 2))
    extra = Column(JSONB, default=lambda: {})
    source = Column(Text)
    created_at = Column(TIMESTAMP(timezone=True), default=func.now())

    # Relationships
    person = relationship("Person", back_populates="events")
    report = relationship("Report", back_populates="events")


class SourceFinding(Base):
    """
    SourceFindings table - rich text/data findings from sources.
    """

    __tablename__ = "source_findings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=func.uuid_generate_v4())
    person_id = Column(UUID(as_uuid=True), ForeignKey("persons.id", ondelete="CASCADE"), nullable=False)
    report_id = Column(UUID(as_uuid=True), ForeignKey("reports.id", ondelete="CASCADE"), nullable=False)
    source_name = Column(Text, nullable=False)
    record_index = Column(Integer)
    data = Column(JSONB, nullable=False)
    raw_text = Column(Text)
    created_at = Column(TIMESTAMP(timezone=True), default=func.now())

    # Relationships
    person = relationship("Person", back_populates="source_findings")
    report = relationship("Report", back_populates="source_findings")

    # Indexes
    __table_args__ = (
        Index("idx_source_findings_person", "person_id"),
        Index("idx_source_findings_source", "source_name"),
        Index("idx_source_findings_data_gin", "data", postgresql_using="gin"),
    )


# =============================================
# ENTITY RESOLUTION TABLES
# =============================================


class PersonLink(Base):
    """
    PersonLinks table - stores entity resolution linking decisions.
    
    Tracks which persons from different reports are believed to be the same real person.
    Used for cross-report deduplication and entity resolution.
    """

    __tablename__ = "person_links"

    id = Column(UUID(as_uuid=True), primary_key=True, default=func.uuid_generate_v4())
    person_a_id = Column(UUID(as_uuid=True), ForeignKey("persons.id", ondelete="CASCADE"), nullable=False)
    person_b_id = Column(UUID(as_uuid=True), ForeignKey("persons.id", ondelete="CASCADE"), nullable=False)
    confidence = Column(Float, nullable=False)  # 0.0-1.0
    match_strategy = Column(Text, nullable=False)  # "exact_passport", "fuzzy_fio", etc.
    is_reviewed = Column(Boolean, default=False)
    is_confirmed = Column(Boolean, nullable=True)
    reviewed_by = Column(Text)
    review_notes = Column(Text)
    created_at = Column(TIMESTAMP(timezone=True), default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), default=func.now(), onupdate=func.now())

    # Relationships
    person_a = relationship("Person", foreign_keys=[person_a_id])
    person_b = relationship("Person", foreign_keys=[person_b_id])

    # Indexes
    __table_args__ = (
        Index("idx_person_links_person_a", "person_a_id"),
        Index("idx_person_links_person_b", "person_b_id"),
        Index("idx_person_links_confidence", "confidence"),
        UniqueConstraint("person_a_id", "person_b_id", name="uq_person_link_pair"),
    )


# =============================================
# EXPORTS
# =============================================

__all__ = [
    "Base",
    "DocType",
    "AddressType",
    "ConnectionType",
    "EventType",
    "Report",
    "Person",
    "Document",
    "Address",
    "Employment",
    "PersonConnection",
    "Vehicle",
    "Event",
    "SourceFinding",
    "PersonLink",
]
