"""Initial migration - create all tables from SQLAlchemy 2.0 models

Revision ID: 001_initial
Revises:
Create Date: 2026-01-01 00:00:00

"""
from __future__ import annotations

from typing import TYPE_CHECKING

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create initial schema - enums, tables, and indexes."""
    # Enable PostgreSQL extensions
    op.execute("CREATE EXTENSION IF NOT EXISTS uuid-ossp")
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")
    op.execute("CREATE EXTENSION IF NOT EXISTS btree_gin")

    # Create enum types
    op.execute(
        "CREATE TYPE doc_type AS ENUM "
        "('passport_rf', 'foreign_passport', 'snils', 'inn', 'oms_policy', 'driver_license', 'other')"
    )
    op.execute(
        "CREATE TYPE address_type AS ENUM "
        "('registration', 'actual', 'work', 'previous', 'birth_place', 'other')"
    )
    op.execute(
        "CREATE TYPE connection_type AS ENUM "
        "('parent', 'child', 'spouse', 'relative', 'travel_companion', 'flight_companion', 'address_cohabitant', 'other')"
    )
    op.execute(
        "CREATE TYPE event_type AS ENUM "
        "('border_crossing_in', 'border_crossing_out', 'flight', 'dtp', 'fssp_debt', 'other')"
    )

    # Create reports table
    op.create_table(
        "reports",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("filename", sa.Text(), nullable=False, unique=True),
        sa.Column("imported_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("report_date", sa.TIMESTAMP(timezone=True)),
        sa.Column("sources_count", sa.Integer()),
        sa.Column("records_count", sa.Integer()),
        sa.Column("main_fio", sa.Text(), nullable=False),
        sa.Column("main_birth_date", sa.Date()),
        sa.Column("raw_header", postgresql.JSONB),
        sa.Column("status", sa.Text(), server_default="imported"),
        sa.Column("warnings", postgresql.JSONB, server_default=sa.text("'[]'::jsonb")),
        sa.Column("created_by", sa.Text()),
    )

    # Create persons table
    op.create_table(
        "persons",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("report_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("fio", sa.Text(), nullable=False),
        sa.Column("birth_date", sa.Date()),
        sa.Column("main_passport", sa.Text()),
        sa.Column("main_snils", sa.Text()),
        sa.Column("main_inn", sa.Text()),
        sa.Column("main_phone", sa.Text()),
        sa.Column("main_email", sa.Text()),
        sa.Column("passport_count", sa.Integer(), server_default="0"),
        sa.Column("phone_count", sa.Integer(), server_default="0"),
        sa.Column("email_count", sa.Integer(), server_default="0"),
        sa.Column("address_count", sa.Integer(), server_default="0"),
        sa.Column("extra_data", postgresql.JSONB, server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["report_id"], ["reports.id"], ondelete="CASCADE"),
    )
    op.create_index("idx_persons_fio_gin", "persons", ["fio"], postgresql_using="gin", postgresql_ops={"fio": "gin_trgm_ops"})
    op.create_index("idx_persons_main_passport", "persons", ["main_passport"])
    op.create_index("idx_persons_main_snils", "persons", ["main_snils"])
    op.create_index("idx_persons_main_inn", "persons", ["main_inn"])
    op.create_index("idx_persons_main_phone", "persons", ["main_phone"])

    # Create documents table
    op.create_table(
        "documents",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("person_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("report_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("doc_type", sa.Enum("PASSPORT_RF", "FOREIGN_PASSPORT", "SNILS", "INN", "OMS_POLICY", "DRIVER_LICENSE", "OTHER", name="doc_type"), nullable=False),
        sa.Column("number", sa.Text(), nullable=False),
        sa.Column("series", sa.Text()),
        sa.Column("issue_date", sa.Date()),
        sa.Column("expiry_date", sa.Date()),
        sa.Column("issuer", sa.Text()),
        sa.Column("issuer_code", sa.Text()),
        sa.Column("status", sa.Text()),
        sa.Column("birth_place", sa.Text()),
        sa.Column("registration_address", sa.Text()),
        sa.Column("extra", postgresql.JSONB, server_default=sa.text("'{}'::jsonb")),
        sa.Column("source_section", sa.Text()),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["person_id"], ["persons.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["report_id"], ["reports.id"], ondelete="CASCADE"),
    )
    op.create_index("idx_documents_person", "documents", ["person_id"])
    op.create_index("idx_documents_number", "documents", ["number"])
    op.create_index("idx_documents_type", "documents", ["doc_type"])
    op.create_unique_constraint("uq_doc_per_report", "documents", ["person_id", "doc_type", "number", "report_id"])

    # Create addresses table
    op.create_table(
        "addresses",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("person_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("report_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("address_type", sa.Enum("REGISTRATION", "ACTUAL", "WORK", "PREVIOUS", "BIRTH_PLACE", "OTHER", name="address_type"), nullable=False),
        sa.Column("full_text", sa.Text(), nullable=False),
        sa.Column("normalized", postgresql.JSONB),
        sa.Column("frequency", sa.Integer(), server_default="1"),
        sa.Column("source", sa.Text()),
        sa.Column("extra", postgresql.JSONB, server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["person_id"], ["persons.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["report_id"], ["reports.id"], ondelete="CASCADE"),
    )
    op.create_index("idx_addresses_person", "addresses", ["person_id"])
    op.create_index("idx_addresses_full_text_gin", "addresses", ["full_text"], postgresql_using="gin", postgresql_ops={"full_text": "gin_trgm_ops"})

    # Create employments table
    op.create_table(
        "employments",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("person_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("report_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("employer_name", sa.Text()),
        sa.Column("employer_inn", sa.Text()),
        sa.Column("employer_ogrn", sa.Text()),
        sa.Column("position", sa.Text()),
        sa.Column("start_date", sa.Date()),
        sa.Column("end_date", sa.Date()),
        sa.Column("salary_annual", sa.Numeric(15, 2)),
        sa.Column("salary_monthly", sa.Numeric(15, 2)),
        sa.Column("source", sa.Text()),
        sa.Column("extra", postgresql.JSONB, server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["person_id"], ["persons.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["report_id"], ["reports.id"], ondelete="CASCADE"),
    )

    # Create person_connections table
    op.create_table(
        "person_connections",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("person_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("report_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("related_fio", sa.Text(), nullable=False),
        sa.Column("related_birth_date", sa.Date()),
        sa.Column("connection_type", sa.Enum("PARENT", "CHILD", "SPOUSE", "RELATIVE", "TRAVEL_COMPANION", "FLIGHT_COMPANION", "ADDRESS_COHABITANT", "OTHER", name="connection_type"), nullable=False),
        sa.Column("source", sa.Text()),
        sa.Column("context", postgresql.JSONB),
        sa.Column("confidence", sa.Float(), server_default="0.8"),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["person_id"], ["persons.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["report_id"], ["reports.id"], ondelete="CASCADE"),
    )

    # Create vehicles table
    op.create_table(
        "vehicles",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("person_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("report_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("gos_number", sa.Text()),
        sa.Column("vin", sa.Text()),
        sa.Column("make_model", sa.Text()),
        sa.Column("year", sa.Integer()),
        sa.Column("extra", postgresql.JSONB, server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["person_id"], ["persons.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["report_id"], ["reports.id"], ondelete="CASCADE"),
    )

    # Create events table
    op.create_table(
        "events",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("person_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("report_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("event_type", sa.Enum("BORDER_CROSSING_IN", "BORDER_CROSSING_OUT", "FLIGHT", "DTP", "FSSP_DEBT", "OTHER", name="event_type"), nullable=False),
        sa.Column("event_date", sa.TIMESTAMP(timezone=True)),
        sa.Column("flight_number", sa.Text()),
        sa.Column("airline", sa.Text()),
        sa.Column("departure", sa.Text()),
        sa.Column("arrival", sa.Text()),
        sa.Column("country", sa.Text()),
        sa.Column("direction", sa.Text()),
        sa.Column("passport_used", sa.Text()),
        sa.Column("companion_fio", sa.Text()),
        sa.Column("debt_amount", sa.Numeric(15, 2)),
        sa.Column("extra", postgresql.JSONB, server_default=sa.text("'{}'::jsonb")),
        sa.Column("source", sa.Text()),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["person_id"], ["persons.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["report_id"], ["reports.id"], ondelete="CASCADE"),
    )

    # Create source_findings table
    op.create_table(
        "source_findings",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("person_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("report_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("source_name", sa.Text(), nullable=False),
        sa.Column("record_index", sa.Integer()),
        sa.Column("data", postgresql.JSONB, nullable=False),
        sa.Column("raw_text", sa.Text()),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["person_id"], ["persons.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["report_id"], ["reports.id"], ondelete="CASCADE"),
    )
    op.create_index("idx_source_findings_person", "source_findings", ["person_id"])
    op.create_index("idx_source_findings_source", "source_findings", ["source_name"])
    op.create_index("idx_source_findings_data_gin", "source_findings", ["data"], postgresql_using="gin")

    # Create view for active documents
    op.execute(
        "CREATE OR REPLACE VIEW v_active_documents AS "
        "SELECT * FROM documents "
        "WHERE status = 'active' OR expiry_date IS NULL OR expiry_date > CURRENT_DATE"
    )


def downgrade() -> None:
    """Drop all tables and enums."""
    # Drop view
    op.execute("DROP VIEW IF EXISTS v_active_documents")

    # Drop tables in reverse order (foreign key dependencies)
    op.drop_table("source_findings")
    op.drop_table("events")
    op.drop_table("vehicles")
    op.drop_table("person_connections")
    op.drop_table("employments")
    op.drop_table("addresses")
    op.drop_table("documents")
    op.drop_table("persons")
    op.drop_table("reports")

    # Drop enum types
    op.execute("DROP TYPE IF EXISTS event_type")
    op.execute("DROP TYPE IF EXISTS connection_type")
    op.execute("DROP TYPE IF EXISTS address_type")
    op.execute("DROP TYPE IF EXISTS doc_type")
