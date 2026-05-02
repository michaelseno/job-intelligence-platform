from __future__ import annotations

from sqlalchemy import select

from app.adapters.base.contracts import AdapterFetchResult, NormalizedJobCandidate
from app.domain.ingestion import IngestionOrchestrator
from app.domain.job_preferences import get_default_job_filter_preferences
from app.domain.transient_ingestion import transient_ingestion_registry
from app.persistence.models import JobDecision, JobPosting, JobSourceLink, Source


class DummyAdapter:
    def __init__(self, jobs):
        self.jobs = jobs

    def validate_config(self, source):
        return []

    def fetch_jobs(self, source):
        return AdapterFetchResult(jobs=self.jobs)


class DummyRegistry:
    def __init__(self, adapter):
        self.adapter = adapter

    def get(self, source_type, adapter_key=None):
        return self.adapter


def make_source(session, name="Example"):
    source = Source(
        name=name,
        source_type="greenhouse",
        base_url=f"https://example.com/{name}",
        dedupe_key=f"greenhouse:{name}",
        is_active=True,
    )
    session.add(source)
    session.commit()
    return source


def make_candidate(external_id="1", title="Senior Python Backend Engineer", url="https://example.com/jobs/1"):
    return NormalizedJobCandidate(
        external_job_id=external_id,
        title=title,
        company_name="Example",
        job_url=url,
        location_text="Remote",
        employment_type="Full-time",
        remote_type="remote",
        description_text="Python backend engineer role. Visa sponsorship available.",
        description_html=None,
        sponsorship_text="Visa sponsorship available",
        posted_at=None,
        raw_payload={"id": external_id},
    )


def test_ingestion_stores_new_untracked_jobs_transiently_without_job_specific_db_records(session):
    source = make_source(session)
    candidate = make_candidate()

    run = IngestionOrchestrator(session, DummyRegistry(DummyAdapter([candidate]))).run_source(source, get_default_job_filter_preferences())

    assert run.jobs_fetched_count == 1
    assert run.jobs_created_count == 0
    assert session.scalar(select(JobPosting).where(JobPosting.job_url == candidate.job_url)) is None
    assert list(session.scalars(select(JobSourceLink))) == []
    assert list(session.scalars(select(JobDecision))) == []
    transient_items = transient_ingestion_registry.list(source.id)
    assert len(transient_items) == 1
    assert transient_items[0].title == candidate.title
    assert transient_items[0].classification.bucket == "matched"


def test_transient_tracking_persists_job_link_decision_and_consumes_entry(session):
    source = make_source(session)
    candidate = make_candidate()
    IngestionOrchestrator(session, DummyRegistry(DummyAdapter([candidate]))).run_source(source, get_default_job_filter_preferences())
    transient_id = transient_ingestion_registry.list(source.id)[0].transient_job_id

    from app.domain.tracking import TrackingService

    job, created = TrackingService(session).track_transient_job(transient_id, "saved", "keep")

    assert created is True
    assert job.tracking_status == "saved"
    assert session.scalar(select(JobSourceLink).where(JobSourceLink.job_posting_id == job.id)) is not None
    assert session.scalar(select(JobDecision).where(JobDecision.job_posting_id == job.id)) is not None
    assert transient_ingestion_registry.get(transient_id) is None
