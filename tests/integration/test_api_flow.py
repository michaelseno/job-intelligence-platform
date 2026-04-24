from __future__ import annotations

from datetime import timedelta

from sqlalchemy import select

from app.persistence.models import JobTrackingEvent, Reminder


class DummyResponse:
    def __init__(self, payload):
        self._payload = payload

    def raise_for_status(self):
        return None

    def json(self):
        return self._payload


def test_manual_source_ingestion_keep_tracking_digest_and_reminders(client, session, monkeypatch):
    greenhouse_payload = {
        "jobs": [
            {
                "id": 42,
                "title": "Senior Python Backend Engineer",
                "absolute_url": "https://example.com/jobs/42",
                "location": {"name": "Remote"},
                "content": "<p>Python backend engineer role. Visa sponsorship available.</p>",
                "updated_at": "2026-04-23T10:00:00Z",
            }
        ]
    }
    monkeypatch.setattr("app.adapters.greenhouse.adapter.httpx.get", lambda *args, **kwargs: DummyResponse(greenhouse_payload))

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
    assert create_response.status_code == 201
    source_id = create_response.json()["id"]

    run_response = client.post(f"/sources/{source_id}/run")
    assert run_response.status_code == 200
    assert run_response.json()["jobs_fetched_count"] == 1

    jobs_response = client.get("/jobs")
    assert jobs_response.status_code == 200
    jobs = jobs_response.json()
    assert len(jobs) == 1
    assert jobs[0]["latest_bucket"] == "matched"
    job_id = jobs[0]["id"]

    keep_response = client.post(f"/jobs/{job_id}/keep")
    assert keep_response.status_code == 200
    assert keep_response.json()["manual_keep"] is True
    assert keep_response.json()["tracking_status"] == "saved"

    tracking_response = client.post(f"/jobs/{job_id}/tracking-status", json={"tracking_status": "applied", "note_text": "Submitted"})
    assert tracking_response.status_code == 200
    assert tracking_response.json()["tracking_status"] == "applied"

    digest_response = client.post("/digest/generate")
    assert digest_response.status_code == 200
    assert digest_response.json()["items"][0]["reason"] == "new_matched"

    events = list(session.scalars(select(JobTrackingEvent)))
    for event in events:
        event.created_at = event.created_at - timedelta(days=8)
        session.add(event)
    session.commit()

    reminders_response = client.post("/reminders/generate")
    assert reminders_response.status_code == 200
    reminders = reminders_response.json()
    assert len(reminders) == 1
    assert reminders[0]["reminder_type"] == "applied_follow_up"

    dismiss_response = client.post(f"/reminders/{reminders[0]['id']}/dismiss")
    assert dismiss_response.status_code == 200
    assert dismiss_response.json()["status"] == "dismissed"


def test_csv_import_mixed_valid_invalid_and_duplicate(client):
    csv_body = "name,source_type,base_url,external_identifier,adapter_key,company_name,is_active,notes\nExample GH,greenhouse,https://boards.greenhouse.io/example,example,,Example,true,\nBad Source,greenhouse,https://boards.greenhouse.io/bad,,,,true,\nExample GH Duplicate,greenhouse,https://boards.greenhouse.io/example,example,,Example,true,\n"

    response = client.post(
        "/sources/import",
        files={"file": ("sources.csv", csv_body, "text/csv")},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["created"] == 1
    assert data["invalid"] == 1
    assert data["skipped_duplicate"] == 1


def test_jobs_api_treats_empty_source_filter_as_unset_and_keeps_integer_filtering(client, monkeypatch):
    greenhouse_payload = {
        "jobs": [
            {
                "id": 77,
                "title": "Senior Backend Engineer",
                "absolute_url": "https://example.com/jobs/77",
                "location": {"name": "Remote"},
                "content": "<p>Backend platform role with Python ownership.</p>",
                "updated_at": "2026-04-23T10:00:00Z",
            }
        ]
    }
    monkeypatch.setattr("app.adapters.greenhouse.adapter.httpx.get", lambda *args, **kwargs: DummyResponse(greenhouse_payload))

    create_response = client.post(
        "/sources",
        json={
            "name": "Example Filter Source",
            "source_type": "greenhouse",
            "base_url": "https://boards.greenhouse.io/filter-example",
            "external_identifier": "filter-example",
            "company_name": "Example",
        },
    )
    assert create_response.status_code == 201
    source_id = create_response.json()["id"]

    run_response = client.post(f"/sources/{source_id}/run")
    assert run_response.status_code == 200

    empty_filter_response = client.get("/jobs?source_id=")
    assert empty_filter_response.status_code == 200
    assert len(empty_filter_response.json()) == 1

    valid_filter_response = client.get(f"/jobs?source_id={source_id}")
    assert valid_filter_response.status_code == 200
    assert len(valid_filter_response.json()) == 1

    invalid_filter_response = client.get("/jobs?source_id=abc")
    assert invalid_filter_response.status_code == 422
