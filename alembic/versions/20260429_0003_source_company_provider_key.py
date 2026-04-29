"""add source company provider uniqueness

Revision ID: 20260429_0003
Revises: 20260424_0002
Create Date: 2026-04-29 10:00:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.orm import Session


revision = "20260429_0003"
down_revision = "20260424_0002"
branch_labels = None
depends_on = None


ACTIVE_COMPANY_PROVIDER_UNIQUE_INDEX = "ix_sources_company_provider_active_unique"


def upgrade() -> None:
    bind = op.get_bind()
    if not _has_column(bind, "sources", "company_provider_key"):
        op.add_column("sources", sa.Column("company_provider_key", sa.String(length=512), nullable=True))

    # Import after the schema change so ORM writes can see the new column. The cleanup is
    # idempotent and soft-deletes only rows in the confirmed source-health cleanup scope.
    from app.domain.source_health_cleanup import cleanup_source_health_sources

    with Session(bind=bind) as session:
        cleanup_source_health_sources(session)

    op.create_index(
        ACTIVE_COMPANY_PROVIDER_UNIQUE_INDEX,
        "sources",
        ["company_provider_key"],
        unique=True,
        sqlite_where=sa.text("deleted_at IS NULL"),
        postgresql_where=sa.text("deleted_at IS NULL"),
    )


def downgrade() -> None:
    op.drop_index(ACTIVE_COMPANY_PROVIDER_UNIQUE_INDEX, table_name="sources")
    op.drop_column("sources", "company_provider_key")


def _has_column(bind, table_name: str, column_name: str) -> bool:
    inspector = sa.inspect(bind)
    return any(column["name"] == column_name for column in inspector.get_columns(table_name))
