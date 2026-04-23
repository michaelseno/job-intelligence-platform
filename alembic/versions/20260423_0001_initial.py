"""initial schema

Revision ID: 20260423_0001
Revises:
Create Date: 2026-04-23 09:00:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260423_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "sources",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("source_type", sa.String(length=50), nullable=False),
        sa.Column("adapter_key", sa.String(length=100), nullable=True),
        sa.Column("company_name", sa.String(length=255), nullable=True),
        sa.Column("base_url", sa.String(length=1024), nullable=False),
        sa.Column("external_identifier", sa.String(length=255), nullable=True),
        sa.Column("config_json", sa.JSON(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("dedupe_key", sa.String(length=1024), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("last_run_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_run_status", sa.String(length=50), nullable=True),
        sa.Column("last_jobs_fetched_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("consecutive_empty_runs", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("health_state", sa.String(length=50), nullable=False, server_default="healthy"),
        sa.Column("health_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("dedupe_key", name="uq_sources_dedupe_key"),
    )
    op.create_index("ix_sources_source_type", "sources", ["source_type"])
    op.create_index("ix_sources_health_state", "sources", ["health_state"])

    op.create_table(
        "source_runs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("source_id", sa.Integer(), sa.ForeignKey("sources.id"), nullable=False),
        sa.Column("trigger_type", sa.String(length=50), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("jobs_fetched_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("jobs_created_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("jobs_updated_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("jobs_unchanged_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("error_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("warning_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("empty_result_flag", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("log_summary", sa.Text(), nullable=True),
        sa.Column("error_details_json", sa.JSON(), nullable=True),
    )
    op.create_index("ix_source_runs_source_id_started_at", "source_runs", ["source_id", "started_at"])

    op.create_table(
        "job_postings",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("canonical_key", sa.String(length=255), nullable=False),
        sa.Column("primary_source_id", sa.Integer(), sa.ForeignKey("sources.id"), nullable=False),
        sa.Column("title", sa.String(length=500), nullable=False),
        sa.Column("company_name", sa.String(length=255), nullable=True),
        sa.Column("job_url", sa.String(length=2048), nullable=False),
        sa.Column("normalized_job_url", sa.String(length=2048), nullable=True),
        sa.Column("location_text", sa.String(length=500), nullable=True),
        sa.Column("employment_type", sa.String(length=255), nullable=True),
        sa.Column("remote_type", sa.String(length=255), nullable=True),
        sa.Column("description_text", sa.Text(), nullable=True),
        sa.Column("description_html", sa.Text(), nullable=True),
        sa.Column("sponsorship_text", sa.Text(), nullable=True),
        sa.Column("posted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("first_seen_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_ingested_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("current_state", sa.String(length=50), nullable=False, server_default="active"),
        sa.Column("latest_bucket", sa.String(length=50), nullable=True),
        sa.Column("latest_score", sa.Integer(), nullable=True),
        sa.Column("latest_decision_id", sa.Integer(), nullable=True),
        sa.Column("manual_keep", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("tracking_status", sa.String(length=50), nullable=True),
    )
    op.create_index("ix_job_postings_canonical_key", "job_postings", ["canonical_key"], unique=True)
    op.create_index("ix_job_postings_latest_bucket", "job_postings", ["latest_bucket"])
    op.create_index("ix_job_postings_tracking_status", "job_postings", ["tracking_status"])

    op.create_table(
        "job_source_links",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("job_posting_id", sa.Integer(), sa.ForeignKey("job_postings.id"), nullable=False),
        sa.Column("source_id", sa.Integer(), sa.ForeignKey("sources.id"), nullable=False),
        sa.Column("source_run_id", sa.Integer(), sa.ForeignKey("source_runs.id"), nullable=False),
        sa.Column("external_job_id", sa.String(length=255), nullable=True),
        sa.Column("source_job_url", sa.String(length=2048), nullable=False),
        sa.Column("raw_payload_json", sa.JSON(), nullable=True),
        sa.Column("content_hash", sa.String(length=64), nullable=False),
        sa.Column("is_primary", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("first_seen_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_job_source_links_job_posting_id", "job_source_links", ["job_posting_id"])
    op.create_index("ix_job_source_links_source_id_external_job_id", "job_source_links", ["source_id", "external_job_id"])

    op.create_table(
        "job_decisions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("job_posting_id", sa.Integer(), sa.ForeignKey("job_postings.id"), nullable=False),
        sa.Column("decision_version", sa.String(length=50), nullable=False),
        sa.Column("bucket", sa.String(length=50), nullable=False),
        sa.Column("final_score", sa.Integer(), nullable=False),
        sa.Column("sponsorship_state", sa.String(length=50), nullable=False),
        sa.Column("decision_reason_summary", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("is_current", sa.Boolean(), nullable=False, server_default=sa.true()),
    )
    op.create_index("ix_job_decisions_job_posting_id_created_at", "job_decisions", ["job_posting_id", "created_at"])

    op.create_table(
        "job_decision_rules",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("job_decision_id", sa.Integer(), sa.ForeignKey("job_decisions.id"), nullable=False),
        sa.Column("rule_key", sa.String(length=100), nullable=False),
        sa.Column("rule_category", sa.String(length=50), nullable=False),
        sa.Column("outcome", sa.String(length=50), nullable=False),
        sa.Column("score_delta", sa.Integer(), nullable=False),
        sa.Column("evidence_snippet", sa.Text(), nullable=True),
        sa.Column("evidence_field", sa.String(length=50), nullable=True),
        sa.Column("explanation_text", sa.Text(), nullable=False),
    )

    op.create_table(
        "job_tracking_events",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("job_posting_id", sa.Integer(), sa.ForeignKey("job_postings.id"), nullable=False),
        sa.Column("event_type", sa.String(length=50), nullable=False),
        sa.Column("tracking_status", sa.String(length=50), nullable=True),
        sa.Column("note_text", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_job_tracking_events_job_posting_id_created_at", "job_tracking_events", ["job_posting_id", "created_at"])

    op.create_table(
        "digests",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("digest_date", sa.Date(), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("generated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("delivery_channel", sa.String(length=50), nullable=False),
        sa.Column("content_summary", sa.Text(), nullable=False),
        sa.UniqueConstraint("digest_date", "delivery_channel", name="uq_digests_date_channel"),
    )

    op.create_table(
        "digest_items",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("digest_id", sa.Integer(), sa.ForeignKey("digests.id"), nullable=False),
        sa.Column("job_posting_id", sa.Integer(), sa.ForeignKey("job_postings.id"), nullable=False),
        sa.Column("bucket", sa.String(length=50), nullable=False),
        sa.Column("reason", sa.String(length=50), nullable=False),
        sa.UniqueConstraint("digest_id", "job_posting_id", name="uq_digest_items_digest_job"),
    )

    op.create_table(
        "reminders",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("job_posting_id", sa.Integer(), sa.ForeignKey("job_postings.id"), nullable=False),
        sa.Column("reminder_type", sa.String(length=50), nullable=False),
        sa.Column("due_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("generated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_reminders_status_due_at", "reminders", ["status", "due_at"])


def downgrade() -> None:
    op.drop_index("ix_reminders_status_due_at", table_name="reminders")
    op.drop_table("reminders")
    op.drop_table("digest_items")
    op.drop_table("digests")
    op.drop_index("ix_job_tracking_events_job_posting_id_created_at", table_name="job_tracking_events")
    op.drop_table("job_tracking_events")
    op.drop_table("job_decision_rules")
    op.drop_index("ix_job_decisions_job_posting_id_created_at", table_name="job_decisions")
    op.drop_table("job_decisions")
    op.drop_index("ix_job_source_links_source_id_external_job_id", table_name="job_source_links")
    op.drop_index("ix_job_source_links_job_posting_id", table_name="job_source_links")
    op.drop_table("job_source_links")
    op.drop_index("ix_job_postings_tracking_status", table_name="job_postings")
    op.drop_index("ix_job_postings_latest_bucket", table_name="job_postings")
    op.drop_index("ix_job_postings_canonical_key", table_name="job_postings")
    op.drop_table("job_postings")
    op.drop_index("ix_source_runs_source_id_started_at", table_name="source_runs")
    op.drop_table("source_runs")
    op.drop_index("ix_sources_health_state", table_name="sources")
    op.drop_index("ix_sources_source_type", table_name="sources")
    op.drop_table("sources")
