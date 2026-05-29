"""Add person_links table for entity resolution.

Revision ID: 002_entity_resolution
Revises: 001_initial
Create Date: 2026-05-29

"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = "002_entity_resolution"
down_revision = "001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create person_links table for entity resolution
    op.create_table(
        "person_links",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("uuid_generate_v4()"),
        ),
        sa.Column(
            "person_a_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKeyConstraint(
                ["person_a_id"],
                ["persons.id"],
                ondelete="CASCADE",
            ),
            nullable=False,
        ),
        sa.Column(
            "person_b_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKeyConstraint(
                ["person_b_id"],
                ["persons.id"],
                ondelete="CASCADE",
            ),
            nullable=False,
        ),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("match_strategy", sa.Text(), nullable=False),
        sa.Column("is_reviewed", sa.Boolean(), server_default="false"),
        sa.Column("is_confirmed", sa.Boolean(), nullable=True),
        sa.Column("reviewed_by", sa.Text(), nullable=True),
        sa.Column("review_notes", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    
    # Create indexes
    op.create_index("idx_person_links_person_a", "person_links", ["person_a_id"])
    op.create_index("idx_person_links_person_b", "person_links", ["person_b_id"])
    op.create_index("idx_person_links_confidence", "person_links", ["confidence"])
    
    # Create unique constraint
    op.create_unique_constraint(
        "uq_person_link_pair",
        "person_links",
        ["person_a_id", "person_b_id"],
    )


def downgrade() -> None:
    op.drop_constraint("uq_person_link_pair", "person_links", type_="unique")
    op.drop_index("idx_person_links_confidence")
    op.drop_index("idx_person_links_person_b")
    op.drop_index("idx_person_links_person_a")
    op.drop_table("person_links")
