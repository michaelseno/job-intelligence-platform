from __future__ import annotations

from sqlalchemy import select

from app.domain.job_visibility import apply_visible_jobs
from app.persistence.models import JobPosting, JobSourceLink, Source, SourceRun, utcnow


def test_visible_jobs_hide_non_retained_deleted_source_jobs_immediately(session):
    source = Source(name="Deleted", source_type="greenhouse", base_url="https://boards.greenhouse.io/deleted", external_identifier="deleted", dedupe_key="deleted", is_active=False, deleted_at=utcnow())
    active_source = Source(name="Active", source_type="greenhouse", base_url="https://boards.greenhouse.io/active", external_identifier="active", dedupe_key="active", is_active=True)
    session.add_all([source, active_source])
    session.commit()
    run = SourceRun(source_id=source.id, trigger_type="manual", status="success")
    session.add(run)
    session.commit()
    retained = JobPosting(canonical_key="retained", primary_source_id=source.id, title="Retained", job_url="https://example.com/retained", latest_bucket="matched", current_state="active")
    hidden = JobPosting(canonical_key="hidden", primary_source_id=source.id, title="Hidden", job_url="https://example.com/hidden", latest_bucket="review", current_state="active")
    visible = JobPosting(canonical_key="visible", primary_source_id=active_source.id, title="Visible", job_url="https://example.com/visible", latest_bucket="review", current_state="active")
    session.add_all([retained, hidden, visible])
    session.flush()
    session.add(JobSourceLink(job_posting_id=hidden.id, source_id=source.id, source_run_id=run.id, source_job_url=hidden.job_url, content_hash="hidden", is_primary=True))
    session.commit()

    visible_jobs = list(session.scalars(apply_visible_jobs(select(JobPosting)).order_by(JobPosting.canonical_key)))

    assert [job.canonical_key for job in visible_jobs] == ["retained", "visible"]
