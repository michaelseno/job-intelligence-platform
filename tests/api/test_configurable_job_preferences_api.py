from __future__ import annotations

from app.domain.job_preferences import get_default_job_filter_preferences
from app.persistence.models import JobPosting, Source


def _payload():
    payload = get_default_job_filter_preferences().model_dump()
    payload["configured_at"] = "2026-04-26T12:00:00.000Z"
    return payload


def test_validate_and_reclassify_accepts_preferences_and_updates_active_jobs(client, session):
    source = Source(name="Test", source_type="greenhouse", base_url="https://example.com", external_identifier="test", dedupe_key="test")
    session.add(source)
    session.flush()
    job = JobPosting(
        canonical_key="job-1",
        primary_source_id=source.id,
        title="Senior Python Backend Engineer",
        company_name="Example",
        job_url="https://example.com/jobs/1",
        normalized_job_url="https://example.com/jobs/1",
        location_text="Remote",
        description_text="Python backend engineer role. Visa sponsorship available. " * 4,
        sponsorship_text="Visa sponsorship available",
    )
    session.add(job)
    session.commit()

    response = client.post("/job-preferences/validate-and-reclassify", json={**_payload(), "next": "/jobs"})

    assert response.status_code == 200
    assert response.json()["reclassification"]["jobs_reclassified"] == 1
    assert response.json()["next"] == "/jobs"
    session.refresh(job)
    assert job.latest_bucket == "matched"
    assert job.latest_score == 34


def test_validate_and_reclassify_rejects_invalid_preferences(client):
    payload = _payload()
    payload["schema_version"] = 2

    response = client.post("/job-preferences/validate-and-reclassify", json=payload)

    assert response.status_code == 422
    assert "schema_version" in response.json()["detail"]["errors"]


def test_jobs_reclassify_requires_preferences(client):
    response = client.post("/jobs/reclassify", json={})

    assert response.status_code == 409


def test_source_run_requires_preferences_before_ingestion(client):
    create_response = client.post(
        "/sources",
        json={
            "name": "Example Greenhouse",
            "source_type": "greenhouse",
            "base_url": "https://boards.greenhouse.io/example",
            "external_identifier": "example",
            "company_name": "Example",
        },
    )
    source_id = create_response.json()["id"]

    response = client.post(f"/sources/{source_id}/run")

    assert response.status_code == 409
