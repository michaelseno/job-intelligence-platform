from __future__ import annotations

import importlib
from datetime import UTC, date, datetime, timedelta
from pathlib import Path

from alembic.migration import MigrationContext
from alembic.operations import Operations
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.persistence.models import (
    Base,
    Digest,
    DigestItem,
    JobDecision,
    JobDecisionRule,
    JobPosting,
    JobSourceLink,
    JobTrackingEvent,
    Reminder,
    Source,
    SourceRun,
)


spec = importlib.util.spec_from_file_location(
    "cleanup_untracked_jobs_migration",
    Path(__file__).resolve().parents[2] / "alembic" / "versions" / "20260501_0005_cleanup_untracked_jobs.py",
)
cleanup_migration = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(cleanup_migration)


def run_cleanup_upgrade(connection):
    context = MigrationContext.configure(connection)
    with Operations.context(context):
        cleanup_migration.upgrade()


def seed_job(session: Session, source: Source, *, key: str, tracking_status: str | None, manual_keep: bool) -> JobPosting:
    job = JobPosting(
        canonical_key=key,
        primary_source_id=source.id,
        title=key,
        company_name="Cleanup Co",
        job_url=f"https://example.com/jobs/{key}",
        normalized_job_url=f"https://example.com/jobs/{key}",
        description_text="cleanup validation",
        manual_keep=manual_keep,
        tracking_status=tracking_status,
    )
    session.add(job)
    session.flush()
    return job


def attach_dependents(session: Session, source: Source, run: SourceRun, digest: Digest, job: JobPosting):
    session.add(JobSourceLink(job_posting_id=job.id, source_id=source.id, source_run_id=run.id, source_job_url=job.job_url, content_hash=f"hash-{job.id}"))
    decision = JobDecision(job_posting_id=job.id, decision_version="mvp_v1", bucket="matched", final_score=1, sponsorship_state="supported", decision_reason_summary="cleanup")
    session.add(decision)
    session.flush()
    session.add(JobDecisionRule(job_decision_id=decision.id, rule_key="qa", rule_category="qa", outcome="matched", score_delta=1, explanation_text="cleanup"))
    session.add(JobTrackingEvent(job_posting_id=job.id, event_type="save", tracking_status=job.tracking_status))
    session.add(Reminder(job_posting_id=job.id, reminder_type="follow_up", due_at=datetime.now(UTC) + timedelta(days=1), status="pending"))
    session.add(DigestItem(digest_id=digest.id, job_posting_id=job.id, bucket="matched", reason="cleanup"))


def test_cleanup_migration_deletes_untracked_dependents_preserves_tracked_and_is_idempotent():
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True, connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        source = Source(name="Cleanup Source", source_type="greenhouse", base_url="https://example.com", dedupe_key="cleanup", is_active=True)
        session.add(source)
        session.flush()
        run = SourceRun(source_id=source.id, trigger_type="manual", status="success")
        digest = Digest(digest_date=date(2026, 5, 1), status="generated", delivery_channel="local", content_summary="cleanup")
        session.add_all([run, digest])
        session.flush()

        untracked_keep = seed_job(session, source, key="untracked-keep", tracking_status=None, manual_keep=True)
        untracked_normal = seed_job(session, source, key="untracked-normal", tracking_status=None, manual_keep=False)
        tracked_keep = seed_job(session, source, key="tracked-keep", tracking_status="saved", manual_keep=True)
        tracked_normal = seed_job(session, source, key="tracked-normal", tracking_status="applied", manual_keep=False)
        for job in [untracked_keep, untracked_normal, tracked_keep, tracked_normal]:
            attach_dependents(session, source, run, digest, job)
        session.commit()

    with engine.begin() as connection:
        run_cleanup_upgrade(connection)
        run_cleanup_upgrade(connection)

    with Session(engine) as session:
        remaining_jobs = {job.canonical_key: job for job in session.scalars(select(JobPosting))}
        assert set(remaining_jobs) == {"tracked-keep", "tracked-normal"}
        assert remaining_jobs["tracked-keep"].manual_keep is True
        assert remaining_jobs["tracked-normal"].tracking_status == "applied"
        remaining_ids = {job.id for job in remaining_jobs.values()}
        for model in [JobSourceLink, JobDecision, JobTrackingEvent, Reminder, DigestItem]:
            rows = list(session.scalars(select(model)))
            assert rows
            assert {row.job_posting_id for row in rows} <= remaining_ids
        remaining_decision_ids = {row.id for row in session.scalars(select(JobDecision))}
        assert {row.job_decision_id for row in session.scalars(select(JobDecisionRule))} <= remaining_decision_ids
