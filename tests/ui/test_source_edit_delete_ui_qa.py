from __future__ import annotations

from app.domain.job_preferences import get_default_job_filter_preferences
from app.persistence.models import JobPosting, JobSourceLink, Source, SourceRun, utcnow


def job_preferences_payload():
    return get_default_job_filter_preferences().model_dump()


class DummyResponse:
    def __init__(self, payload):
        self._payload = payload

    def raise_for_status(self):
        return None

    def json(self):
        return self._payload


def create_source(client, *, name: str, base_slug: str, is_active: bool = True):
    response = client.post(
        "/sources",
        json={
            "name": name,
            "source_type": "greenhouse",
            "base_url": f"https://boards.greenhouse.io/{base_slug}",
            "external_identifier": base_slug,
            "company_name": name,
            "is_active": is_active,
        },
    )
    assert response.status_code == 201
    return response.json()


def track_first_transient_job(client, source_id: int, *, tracking_status: str = "saved") -> int:
    transient_response = client.get(f"/ingestion/transient-jobs?source_id={source_id}")
    assert transient_response.status_code == 200
    transient_jobs = transient_response.json()["items"]
    assert len(transient_jobs) == 1
    track_response = client.post(
        f"/ingestion/transient-jobs/{transient_jobs[0]['transient_job_id']}/tracking-status",
        json={"tracking_status": tracking_status},
    )
    assert track_response.status_code == 201
    return track_response.json()["persisted_job_id"]


def test_sources_html_exposes_edit_and_delete_actions_from_list_and_detail(client):
    source = create_source(client, name="List Action Source", base_slug="list-action-source")

    list_response = client.get("/sources", headers={"accept": "text/html"})
    assert list_response.status_code == 200
    assert f'/sources/{source["id"]}/edit' in list_response.text
    assert f'/sources/{source["id"]}/delete' in list_response.text

    detail_response = client.get(f"/sources/{source['id']}", headers={"accept": "text/html"})
    assert detail_response.status_code == 200
    assert "Edit source" in detail_response.text
    assert "Delete source" in detail_response.text


def test_source_delete_confirmation_explains_async_cleanup_and_retention(client, monkeypatch):
    greenhouse_payload = {
        "jobs": [
            {
                "id": 501,
                "title": "Historical QA Automation Engineer",
                "absolute_url": "https://example.com/jobs/501",
                "location": {"name": "Remote"},
                "content": "<p>QA automation regression role. Sponsorship is mentioned but remains unclear.</p>",
                "updated_at": "2026-04-23T10:00:00Z",
            }
        ]
    }
    monkeypatch.setattr("app.adapters.greenhouse.adapter.httpx.get", lambda *args, **kwargs: DummyResponse(greenhouse_payload))

    source = create_source(client, name="Historical Source", base_slug="historical-source")

    run_response = client.post(f"/sources/{source['id']}/run", json={"job_preferences": job_preferences_payload()})
    assert run_response.status_code == 200

    job_id = track_first_transient_job(client, source["id"])

    tracking_response = client.post(
        f"/jobs/{job_id}/tracking-status",
        json={"tracking_status": "saved", "note_text": "Keep for history"},
    )
    assert tracking_response.status_code == 200

    delete_page = client.get(f"/sources/{source['id']}/delete", headers={"accept": "text/html"})
    assert delete_page.status_code == 200
    assert "Historical Source" in delete_page.text
    assert "permanently removes most jobs from this source" in delete_page.text
    assert "cleaned up in the background" in delete_page.text
    assert "Only jobs that are both Matched and Active will be retained" in delete_page.text
    assert "Tracking status, reminders, manual keep, and digest inclusion do not preserve a job" in delete_page.text


def test_source_delete_success_flash_mentions_cleanup_and_hidden_jobs(client, monkeypatch):
    monkeypatch.setattr("app.web.routes.run_source_delete_cleanup", lambda source_id: None)

    source = create_source(client, name="Cleanup Flash Source", base_slug="cleanup-flash-source")

    delete_response = client.post(
        f"/sources/{source['id']}/delete",
        headers={"content-type": "application/x-www-form-urlencoded", "accept": "text/html"},
        data={},
        follow_redirects=True,
    )
    assert delete_response.status_code == 200
    assert "Source deleted. Job cleanup has started" in delete_response.text
    assert "non-retained jobs from this source are hidden from Dashboard and Jobs now" in delete_response.text
    assert "Matched active jobs may remain" in delete_response.text


def test_retained_job_marks_deleted_source_provenance_as_historical(client, session):
    source = create_source(client, name="Deleted Provenance Source", base_slug="deleted-provenance-source")
    source_id = source["id"]

    run = SourceRun(source_id=source_id, trigger_type="manual", status="success")
    session.add(run)
    session.flush()

    now = utcnow()
    job = JobPosting(
        canonical_key="deleted-provenance-source:matched-active",
        primary_source_id=source_id,
        title="Matched Active Role",
        company_name="Deleted Provenance Source",
        job_url="https://example.com/jobs/matched-active",
        normalized_job_url="https://example.com/jobs/matched-active",
        location_text="Remote",
        description_text="Retained matched active job.",
        current_state="active",
        latest_bucket="matched",
        latest_score=91,
        first_seen_at=now,
        last_seen_at=now,
        last_ingested_at=now,
    )
    session.add(job)
    session.flush()

    session.add(
        JobSourceLink(
            job_posting_id=job.id,
            source_id=source_id,
            source_run_id=run.id,
            external_job_id="matched-active",
            source_job_url="https://example.com/jobs/matched-active",
            content_hash="deleted-provenance-source-hash",
            is_primary=True,
            first_seen_at=now,
            last_seen_at=now,
        )
    )
    db_source = session.get(Source, source_id)
    db_source.deleted_at = utcnow()
    db_source.is_active = False
    session.commit()

    jobs_page = client.get("/jobs", headers={"accept": "text/html"})
    assert jobs_page.status_code == 200
    assert "Matched Active Role" in jobs_page.text
    assert "Deleted source" in jobs_page.text

    source_filter_page = client.get(f"/jobs?source_id={source_id}", headers={"accept": "text/html"})
    assert source_filter_page.status_code == 200
    assert f'<option value="{source_id}"' not in source_filter_page.text

    job_page = client.get(f"/jobs/{job.id}", headers={"accept": "text/html"})
    assert job_page.status_code == 200
    assert "Deleted Provenance Source" in job_page.text
    assert "Deleted source" in job_page.text
    assert f'/sources/{source_id}/edit' not in job_page.text
    assert f'/sources/{source_id}/run' not in job_page.text


def test_deleted_source_non_retained_job_uses_normal_not_found(client, monkeypatch):
    monkeypatch.setattr("app.web.routes.run_source_delete_cleanup", lambda source_id: None)

    greenhouse_payload = {
        "jobs": [
            {
                "id": 501,
                "title": "Deleted Cleanup QA Automation Engineer",
                "absolute_url": "https://example.com/jobs/501",
                "location": {"name": "Remote"},
                "content": "<p>QA automation cleanup regression role. Sponsorship is mentioned but remains unclear.</p>",
                "updated_at": "2026-04-23T10:00:00Z",
            }
        ]
    }
    monkeypatch.setattr("app.adapters.greenhouse.adapter.httpx.get", lambda *args, **kwargs: DummyResponse(greenhouse_payload))

    source = create_source(client, name="Deleted Cleanup Source", base_slug="deleted-cleanup-source")

    run_response = client.post(f"/sources/{source['id']}/run", json={"job_preferences": job_preferences_payload()})
    assert run_response.status_code == 200

    job_id = track_first_transient_job(client, source["id"])

    delete_response = client.post(
        f"/sources/{source['id']}/delete",
        headers={"content-type": "application/x-www-form-urlencoded", "accept": "text/html"},
        data={},
        follow_redirects=False,
    )
    assert delete_response.status_code == 303

    deleted_job_page = client.get(f"/jobs/{job_id}", headers={"accept": "text/html"})
    assert deleted_job_page.status_code == 404
