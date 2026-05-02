from __future__ import annotations

from sqlalchemy import select

from app.adapters.base.contracts import AdapterFetchResult, NormalizedJobCandidate
from app.domain.ingestion import IngestionOrchestrator
from app.domain.job_preferences import get_default_job_filter_preferences
from app.domain.transient_ingestion import transient_ingestion_registry
from app.persistence.models import JobDecision, JobDecisionRule, JobPosting, JobSourceLink, JobTrackingEvent, Source


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


def make_source(session, name="QA Transient"):
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


def make_candidate(external_id="qa-1", title="QA Transient Backend Engineer", url="https://example.com/jobs/qa-1"):
    return NormalizedJobCandidate(
        external_job_id=external_id,
        title=title,
        company_name="QA Co",
        job_url=url,
        location_text="Remote",
        employment_type="Full-time",
        remote_type="remote",
        description_text="Python backend engineer role with visa sponsorship available.",
        description_html=None,
        sponsorship_text="Visa sponsorship available",
        posted_at=None,
        raw_payload={"id": external_id, "title": title},
    )


def run_ingestion(session, source, jobs):
    return IngestionOrchestrator(session, DummyRegistry(DummyAdapter(jobs))).run_source(
        source,
        get_default_job_filter_preferences(),
    )


def test_transient_api_refresh_restart_and_invalid_tracking_paths(client, session):
    source = make_source(session)
    first = make_candidate("qa-a", "QA Temporary A", "https://example.com/jobs/qa-a")
    second = make_candidate("qa-b", "QA Temporary B", "https://example.com/jobs/qa-b")

    run_ingestion(session, source, [first])
    list_response = client.get("/ingestion/transient-jobs")
    assert list_response.status_code == 200
    first_items = list_response.json()["items"]
    assert len(first_items) == 1
    first_id = first_items[0]["transient_job_id"]
    assert first_items[0]["tracking_status"] is None
    assert client.get(f"/ingestion/transient-jobs/{first_id}").status_code == 200

    invalid_response = client.post(f"/ingestion/transient-jobs/{first_id}/tracking-status", json={"tracking_status": ""})
    assert invalid_response.status_code == 400
    assert session.scalar(select(JobPosting).where(JobPosting.job_url == first.job_url)) is None
    assert transient_ingestion_registry.get(first_id) is not None

    run_ingestion(session, source, [second])
    refreshed = client.get("/ingestion/transient-jobs").json()["items"]
    assert len(refreshed) == 1
    assert refreshed[0]["title"] == "QA Temporary B"
    assert client.get(f"/ingestion/transient-jobs/{first_id}").status_code == 404

    second_id = refreshed[0]["transient_job_id"]
    transient_ingestion_registry.clear()
    assert client.get("/ingestion/transient-jobs").json()["items"] == []
    assert client.get(f"/ingestion/transient-jobs/{second_id}").status_code == 404
    assert session.scalar(select(JobPosting).where(JobPosting.job_url == second.job_url)) is None


def test_api_tracking_transient_persists_related_records_and_survives_registry_restart(client, session):
    source = make_source(session)
    candidate = make_candidate("qa-save", "QA Track Me", "https://example.com/jobs/qa-save")
    run = run_ingestion(session, source, [candidate])
    transient_id = client.get("/ingestion/transient-jobs").json()["items"][0]["transient_job_id"]

    response = client.post(
        f"/ingestion/transient-jobs/{transient_id}/tracking-status",
        json={"tracking_status": "interview", "note_text": "QA validation"},
    )

    assert response.status_code == 201
    body = response.json()
    job_id = body["id"]
    job = session.get(JobPosting, job_id)
    assert job is not None
    assert job.tracking_status == "interview"
    link = session.scalar(select(JobSourceLink).where(JobSourceLink.job_posting_id == job_id))
    assert link is not None
    assert link.source_run_id == run.id
    assert link.external_job_id == "qa-save"
    decision = session.scalar(select(JobDecision).where(JobDecision.job_posting_id == job_id))
    assert decision is not None
    assert session.scalar(select(JobDecisionRule).where(JobDecisionRule.job_decision_id == decision.id)) is not None
    event = session.scalar(select(JobTrackingEvent).where(JobTrackingEvent.job_posting_id == job_id))
    assert event is not None
    assert event.tracking_status == "interview"
    assert client.get(f"/ingestion/transient-jobs/{transient_id}").status_code == 404

    transient_ingestion_registry.clear()
    assert session.get(JobPosting, job_id).tracking_status == "interview"
    assert client.get(f"/jobs/{job_id}").status_code == 200


def test_existing_tracked_match_updates_without_transient_duplicate(session):
    source = make_source(session)
    tracked = JobPosting(
        canonical_key="tracked-qa",
        primary_source_id=source.id,
        title="Old Title",
        company_name="QA Co",
        job_url="https://example.com/jobs/tracked-qa",
        normalized_job_url="https://example.com/jobs/tracked-qa",
        description_text="Old description",
        tracking_status="saved",
    )
    session.add(tracked)
    session.commit()

    updated = make_candidate("tracked-qa", "Updated Tracked Title", "https://example.com/jobs/tracked-qa")
    run = run_ingestion(session, source, [updated])

    session.refresh(tracked)
    assert run.jobs_updated_count == 1
    assert tracked.id is not None
    assert tracked.title == "Updated Tracked Title"
    assert tracked.tracking_status == "saved"
    assert len(transient_ingestion_registry.list(source.id)) == 0
    assert session.scalar(select(JobSourceLink).where(JobSourceLink.job_posting_id == tracked.id)) is not None
