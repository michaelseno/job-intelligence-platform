"""cleanup untracked persisted jobs

Revision ID: 20260501_0005
Revises: 20260429_0004
Create Date: 2026-05-01 00:00:00
"""

from __future__ import annotations

from alembic import op
from sqlalchemy import bindparam, text


revision = "20260501_0005"
down_revision = "20260429_0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    target_job_ids = [row[0] for row in bind.execute(text("SELECT id FROM job_postings WHERE tracking_status IS NULL")).fetchall()]
    if not target_job_ids:
        return

    decision_ids = [
        row[0]
        for row in bind.execute(
            text("SELECT id FROM job_decisions WHERE job_posting_id IN :job_ids").bindparams(bindparam("job_ids", expanding=True)),
            {"job_ids": target_job_ids},
        ).fetchall()
    ]
    if decision_ids:
        bind.execute(
            text("DELETE FROM job_decision_rules WHERE job_decision_id IN :decision_ids").bindparams(bindparam("decision_ids", expanding=True)),
            {"decision_ids": decision_ids},
        )

    for table in ("job_decisions", "job_tracking_events", "reminders", "digest_items", "job_source_links"):
        bind.execute(
            text(f"DELETE FROM {table} WHERE job_posting_id IN :job_ids").bindparams(bindparam("job_ids", expanding=True)),
            {"job_ids": target_job_ids},
        )
    bind.execute(
        text("DELETE FROM job_postings WHERE id IN :job_ids AND tracking_status IS NULL").bindparams(bindparam("job_ids", expanding=True)),
        {"job_ids": target_job_ids},
    )


def downgrade() -> None:
    # Irreversible data cleanup: deleted untracked jobs and dependents cannot be restored.
    pass
