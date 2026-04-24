"""add sources soft-delete schema

Revision ID: 20260424_0002
Revises: 20260423_0001
Create Date: 2026-04-24 10:00:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260424_0002"
down_revision = "20260423_0001"
branch_labels = None
depends_on = None


ACTIVE_SOURCE_UNIQUE_INDEX = "ix_sources_dedupe_key_active_unique"
LEGACY_SOURCE_UNIQUE_CONSTRAINT = "uq_sources_dedupe_key"


def upgrade() -> None:
    bind = op.get_bind()

    if bind.dialect.name == "sqlite":
        with op.batch_alter_table("sources") as batch_op:
            batch_op.add_column(sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True))
            batch_op.drop_constraint(LEGACY_SOURCE_UNIQUE_CONSTRAINT, type_="unique")
    else:
        op.add_column("sources", sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True))
        op.drop_constraint(LEGACY_SOURCE_UNIQUE_CONSTRAINT, "sources", type_="unique")

    op.create_index(
        ACTIVE_SOURCE_UNIQUE_INDEX,
        "sources",
        ["dedupe_key"],
        unique=True,
        sqlite_where=sa.text("deleted_at IS NULL"),
        postgresql_where=sa.text("deleted_at IS NULL"),
    )


def downgrade() -> None:
    op.drop_index(ACTIVE_SOURCE_UNIQUE_INDEX, table_name="sources")

    bind = op.get_bind()

    if bind.dialect.name == "sqlite":
        with op.batch_alter_table("sources") as batch_op:
            batch_op.create_unique_constraint(LEGACY_SOURCE_UNIQUE_CONSTRAINT, ["dedupe_key"])
            batch_op.drop_column("deleted_at")
    else:
        op.create_unique_constraint(LEGACY_SOURCE_UNIQUE_CONSTRAINT, "sources", ["dedupe_key"])
        op.drop_column("sources", "deleted_at")
