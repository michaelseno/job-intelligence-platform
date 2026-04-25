from __future__ import annotations

from datetime import timedelta

from sqlalchemy import select

from app.domain.source_cleanup import SOURCE_DELETE_CLEANUP_TRIGGER, SourceDeleteCleanupService
from app.persistence.models import (
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
    utcnow,
)


def _source(session, name="Deleted Source"):
    source = Source(
        name=name,
        source_type="greenhouse",
        base_url=f"https://boards.greenhouse.io/{name.lower().replace(' ', '-')}",
        external_identifier=name.lower().replace(" ", "-"),
        dedupe_key=name.lower().replace(" ", "-"),
        is_active=True,
    )
    session.add(source)
    session.commit()
    return source


def _run(session, source):
    run = SourceRun(source_id=source.id, trigger_type="manual", status="success")
    session.add(run)
    session.commit()
    return run


def _job(session, source, run, key, bucket, state="active", *, link_source=None, primary=True, tracked=False, keep=False):
    job = JobPosting(
        canonical_key=key,
        primary_source_id=source.id,
        title=key,
        company_name="Acme",
        job_url=f"https://example.com/{key}",
        current_state=state,
        latest_bucket=bucket,
        manual_keep=keep,
        tracking_status="saved" if tracked else None,
    )
    session.add(job)
    session.flush()
    decision = JobDecision(
        job_posting_id=job.id,
        decision_version="v1",
        bucket=bucket or "review",
        final_score=80,
        sponsorship_state="unknown",
        decision_reason_summary="summary",
        is_current=True,
    )
    session.add(decision)
    session.flush()
    job.latest_decision_id = decision.id
    session.add(JobDecisionRule(job_decision_id=decision.id, rule_key="r", rule_category="c", outcome="matched", score_delta=1, explanation_text="e"))
    session.add(
        JobSourceLink(
            job_posting_id=job.id,
            source_id=(link_source or source).id,
            source_run_id=run.id,
            source_job_url=job.job_url,
            content_hash=key,
            is_primary=primary,
        )
    )
    if tracked:
        session.add(JobTrackingEvent(job_posting_id=job.id, event_type="status_change", tracking_status="saved"))
        session.add(Reminder(job_posting_id=job.id, reminder_type="saved_follow_up", due_at=utcnow() + timedelta(days=1), status="pending"))
        digest = Digest(digest_date=utcnow().date(), status="generated", delivery_channel="in_app", content_summary="")
        session.add(digest)
        session.flush()
        session.add(DigestItem(digest_id=digest.id, job_posting_id=job.id, bucket=bucket or "review", reason="new_review"))
    session.commit()
    return job


def test_cleanup_retains_only_matched_active_and_deletes_dependents(session):
    source = _source(session)
    run = _run(session, source)
    retained = _job(session, source, run, "matched-active", "matched", "active", tracked=True)
    delete_matrix = [
        _job(session, source, run, "matched-closed", "matched", "closed"),
        _job(session, source, run, "review-active", "review", "active", tracked=True, keep=True),
        _job(session, source, run, "rejected-active", "rejected", "active"),
        _job(session, source, run, "unclassified-active", None, "active"),
    ]
    source.deleted_at = utcnow()
    source.is_active = False
    session.add(source)
    session.commit()
    retained_id = retained.id
    deleted_ids = [job.id for job in delete_matrix]

    result = SourceDeleteCleanupService(session).cleanup_source(source.id)

    assert result.status == "success"
    assert result.associated_count == 5
    assert result.retained_count == 1
    assert result.deleted_count == 4
    assert session.get(JobPosting, retained_id) is not None
    for deleted_id in deleted_ids:
        assert session.get(JobPosting, deleted_id) is None
    assert list(session.scalars(select(JobSourceLink).where(JobSourceLink.job_posting_id.in_(deleted_ids)))) == []
    assert list(session.scalars(select(JobDecision).where(JobDecision.job_posting_id.in_(deleted_ids)))) == []
    assert list(session.scalars(select(JobTrackingEvent).where(JobTrackingEvent.job_posting_id.in_(deleted_ids)))) == []
    assert list(session.scalars(select(Reminder).where(Reminder.job_posting_id.in_(deleted_ids)))) == []
    assert list(session.scalars(select(DigestItem).where(DigestItem.job_posting_id.in_(deleted_ids)))) == []

    cleanup_run = session.scalar(select(SourceRun).where(SourceRun.trigger_type == SOURCE_DELETE_CLEANUP_TRIGGER))
    assert cleanup_run is not None
    assert cleanup_run.status == "success"
    assert cleanup_run.error_details_json["deleted_count"] == 4


def test_cleanup_is_idempotent_and_handles_link_only_association(session):
    deleted_source = _source(session, "Deleted Link Source")
    active_source = _source(session, "Active Source")
    run = _run(session, deleted_source)
    retained = _job(session, active_source, run, "link-retained", "matched", "active", link_source=deleted_source, primary=False)
    deleted = _job(session, active_source, run, "link-deleted", "review", "active", link_source=deleted_source, primary=False)
    deleted_source.deleted_at = utcnow()
    deleted_source.is_active = False
    session.add(deleted_source)
    session.commit()
    retained_id = retained.id
    deleted_id = deleted.id

    first = SourceDeleteCleanupService(session).cleanup_source(deleted_source.id)
    second = SourceDeleteCleanupService(session).cleanup_source(deleted_source.id)

    assert first.deleted_count == 1
    assert second.deleted_count == 0
    assert session.get(JobPosting, retained_id) is not None
    assert session.get(JobPosting, deleted_id) is None


def test_cleanup_skips_non_deleted_source(session):
    source = _source(session)
    run = _run(session, source)
    job = _job(session, source, run, "not-deleted-source-job", "review", "active")

    result = SourceDeleteCleanupService(session).cleanup_source(source.id)

    assert result.status == "skipped_source_not_deleted"
    assert session.get(JobPosting, job.id) is not None
