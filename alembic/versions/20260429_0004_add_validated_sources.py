"""add validated source health sources

Revision ID: 20260429_0004
Revises: 20260429_0003
Create Date: 2026-04-29 11:00:00
"""

from __future__ import annotations

from alembic import op
from sqlalchemy.orm import Session


revision = "20260429_0004"
down_revision = "20260429_0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    from app.domain.source_seed import add_validated_source_additions

    bind = op.get_bind()
    with Session(bind=bind) as session:
        add_validated_source_additions(session)


def downgrade() -> None:
    # Source additions are intentionally not deleted on downgrade to avoid removing
    # operator-managed rows or source run history that may have accumulated after seeding.
    pass
