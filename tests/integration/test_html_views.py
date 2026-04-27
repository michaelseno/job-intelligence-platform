from __future__ import annotations

from app.domain.job_preferences import get_default_job_filter_preferences


def job_preferences_payload():
    return get_default_job_filter_preferences().model_dump()


class DummyResponse:
    def __init__(self, payload):
        self._payload = payload

    def raise_for_status(self):
        return None

    def json(self):
        return self._payload


def seed_job(client, monkeypatch):
    greenhouse_payload = {
        "jobs": [
            {
                "id": 99,
                "title": "QA Automation Engineer",
                "absolute_url": "https://example.com/jobs/99",
                "location": {"name": "Remote, Spain"},
                "content": "<p>QA automation role with Python testing ownership. Sponsorship is unclear for this role.</p>",
                "updated_at": "2026-04-23T10:00:00Z",
            }
        ]
    }
    monkeypatch.setattr("app.adapters.greenhouse.adapter.httpx.get", lambda *args, **kwargs: DummyResponse(greenhouse_payload))
    source = client.post(
        "/sources",
        json={
            "name": "Example Greenhouse",
            "source_type": "greenhouse",
            "base_url": "https://boards.greenhouse.io/example",
            "external_identifier": "example",
            "company_name": "Example",
        },
    ).json()
    client.post(f"/sources/{source['id']}/run", json={"job_preferences": job_preferences_payload()})
    return client.get("/jobs").json()[0]


def seed_job_with_source(client, monkeypatch):
    greenhouse_payload = {
        "jobs": [
            {
                "id": 100,
                "title": "Python Backend Engineer",
                "absolute_url": "https://example.com/jobs/100",
                "location": {"name": "Remote"},
                "content": "<p>Platform engineering role with Python and backend ownership. Visa sponsorship available.</p>",
                "updated_at": "2026-04-23T11:00:00Z",
            }
        ]
    }
    monkeypatch.setattr("app.adapters.greenhouse.adapter.httpx.get", lambda *args, **kwargs: DummyResponse(greenhouse_payload))
    source = client.post(
        "/sources",
        json={
            "name": "Filterable Greenhouse",
            "source_type": "greenhouse",
            "base_url": "https://boards.greenhouse.io/filterable",
            "external_identifier": "filterable",
            "company_name": "Filterable",
        },
    ).json()
    client.post(f"/sources/{source['id']}/run", json={"job_preferences": job_preferences_payload()})
    job = client.get("/jobs").json()[0]
    return source, job


def test_dashboard_and_jobs_html_render(client, monkeypatch):
    seed_job(client, monkeypatch)

    dashboard_response = client.get("/dashboard", headers={"accept": "text/html"})
    assert dashboard_response.status_code == 200
    assert "Dashboard" in dashboard_response.text
    assert "Rejected" not in dashboard_response.text
    assert "Jobs needing attention" in dashboard_response.text

    jobs_response = client.get("/jobs", headers={"accept": "text/html"})
    assert jobs_response.status_code == 200
    assert "Bucket" in jobs_response.text
    assert "Tracking" in jobs_response.text
    assert "QA Automation Engineer" in jobs_response.text


def test_html_forms_redirect_for_source_and_tracking(client, monkeypatch):
    create_response = client.post(
        "/sources",
        headers={"content-type": "application/x-www-form-urlencoded", "accept": "text/html"},
        data={
            "name": "Manual Lever",
            "source_type": "lever",
            "base_url": "https://jobs.lever.co/example",
            "external_identifier": "example",
            "company_name": "Example",
            "is_active": "on",
        },
        follow_redirects=False,
    )
    assert create_response.status_code == 303
    assert create_response.headers["location"].startswith("/sources?")

    job = seed_job(client, monkeypatch)
    tracking_response = client.post(
        f"/jobs/{job['id']}/tracking-status",
        headers={"content-type": "application/x-www-form-urlencoded", "accept": "text/html"},
        data={"tracking_status": "saved", "next": "/jobs"},
        follow_redirects=False,
    )
    assert tracking_response.status_code == 303
    assert tracking_response.headers["location"].startswith("/jobs?")


def test_jobs_html_treats_empty_source_filter_as_unset(client, monkeypatch):
    _, job = seed_job_with_source(client, monkeypatch)

    response = client.get("/jobs?source_id=", headers={"accept": "text/html"})

    assert response.status_code == 200
    assert job["title"] in response.text
