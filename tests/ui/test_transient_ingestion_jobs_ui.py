from __future__ import annotations

from datetime import UTC, datetime

from bs4 import BeautifulSoup

from app.domain.classification import ClassificationSnapshot, RuleResult
from app.domain.transient_ingestion import TransientIngestionJob, transient_ingestion_registry
from app.persistence.models import JobPosting, JobSourceLink, Source, SourceRun


def seed_source_and_run(session):
    source = Source(
        name="Transient UI Source",
        source_type="greenhouse",
        base_url="https://boards.greenhouse.io/transient-ui",
        external_identifier="transient-ui",
        dedupe_key="transient-ui",
        is_active=True,
    )
    session.add(source)
    session.commit()
    run = SourceRun(source_id=source.id, trigger_type="manual", status="success")
    session.add(run)
    session.commit()
    return source, run


def seed_tracked_job(session, source, run):
    job = JobPosting(
        canonical_key="tracked-ui-job",
        primary_source_id=source.id,
        title="Tracked Backend Engineer",
        company_name="TrackedCo",
        job_url="https://example.com/tracked-ui-job",
        latest_bucket="matched",
        latest_score=42,
        current_state="active",
        tracking_status="saved",
    )
    session.add(job)
    session.flush()
    session.add(
        JobSourceLink(
            job_posting_id=job.id,
            source_id=source.id,
            source_run_id=run.id,
            source_job_url=job.job_url,
            content_hash="tracked-hash",
            is_primary=True,
        )
    )
    session.commit()
    return job


def make_transient_job(source, run):
    now = datetime(2026, 5, 1, 12, 0, tzinfo=UTC)
    return TransientIngestionJob(
        transient_job_id="temporary-ui-job-1",
        source_id=source.id,
        source_run_id=run.id,
        external_job_id="temporary-1",
        canonical_key="temporary-ui-job",
        normalized_job_url="https://example.com/temporary-ui-job",
        title="Temporary Python Engineer",
        company_name="TempCo",
        job_url="https://example.com/temporary-ui-job",
        location_text="Remote",
        employment_type="Full-time",
        remote_type="remote",
        description_text="Python backend role with visa sponsorship available.",
        description_html=None,
        sponsorship_text="Visa sponsorship available",
        posted_at=None,
        raw_payload={"id": "temporary-1"},
        classification=ClassificationSnapshot(
            decision_version="mvp_v1",
            bucket="matched",
            final_score=54,
            sponsorship_state="supported",
            decision_reason_summary="Role aligns with target backend preferences.",
            rules=[
                RuleResult(
                    rule_key="python_backend",
                    rule_category="role_positive",
                    outcome="matched",
                    score_delta=18,
                    evidence_snippet="Python backend role",
                    evidence_field="description_text",
                    explanation_text="Role aligns with Python backend target.",
                )
            ],
        ),
        first_seen_at=now,
        last_seen_at=now,
        created_at=now,
    )


def parse_html(response):
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")
    return BeautifulSoup(response.text, "html.parser")


def test_jobs_page_shows_mixed_persisted_and_temporary_results(client, session):
    source, run = seed_source_and_run(session)
    tracked = seed_tracked_job(session, source, run)
    transient_ingestion_registry.replace_source_results(source.id, [make_transient_job(source, run)])

    response = client.get("/jobs", headers={"accept": "text/html"})
    soup = parse_html(response)

    assert "Temporary ingestion results" in response.text
    assert "2 jobs shown: 1 tracked, 1 temporary from the latest ingestion run." in response.text
    assert "Tracked Backend Engineer" in response.text
    assert "Temporary Python Engineer" in response.text
    assert soup.find("span", string="Temporary") is not None
    assert "This is a temporary untracked ingestion result. Track it to save it." in response.text
    assert f'href="/jobs/{tracked.id}"' in response.text
    assert 'href="/jobs/transient/temporary-ui-job-1"' in response.text
    assert 'href="/jobs/temporary-ui-job-1"' not in response.text


def test_transient_tracking_form_posts_to_transient_endpoint(client, session):
    source, run = seed_source_and_run(session)
    transient_ingestion_registry.replace_source_results(source.id, [make_transient_job(source, run)])

    response = client.get("/jobs", headers={"accept": "text/html"})
    soup = parse_html(response)

    form = soup.find("form", {"action": "/ingestion/transient-jobs/temporary-ui-job-1/tracking-status"})
    assert form is not None
    assert form.get("data-transient-tracking-form") == ""
    assert form.find("label", string="Tracking status for Temporary Python Engineer") is not None
    assert form.find("button").get_text(strip=True) == "Track job"


def test_transient_detail_uses_runtime_safe_route(client, session):
    source, run = seed_source_and_run(session)
    transient_ingestion_registry.replace_source_results(source.id, [make_transient_job(source, run)])

    response = client.get("/jobs/transient/temporary-ui-job-1", headers={"accept": "text/html"})

    assert response.status_code == 200
    assert "Temporary ingestion result" in response.text
    assert "Temporary Python Engineer" in response.text
    assert "/ingestion/transient-jobs/temporary-ui-job-1/tracking-status" in response.text


def test_missing_transient_detail_shows_unavailable_error(client):
    response = client.get("/jobs/transient/missing", headers={"accept": "text/html"})

    assert response.status_code == 404
    assert "Temporary job unavailable" in response.text
    assert "This temporary result is no longer available." in response.text
