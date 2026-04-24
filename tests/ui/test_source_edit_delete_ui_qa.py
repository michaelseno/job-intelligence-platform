from __future__ import annotations


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


def test_deleted_source_preserves_historical_job_pages_and_delete_warning_context(client, monkeypatch):
    greenhouse_payload = {
        "jobs": [
            {
                "id": 501,
                "title": "Historical Safety Engineer",
                "absolute_url": "https://example.com/jobs/501",
                "location": {"name": "Remote"},
                "content": "<p>Historical safety regression role.</p>",
                "updated_at": "2026-04-23T10:00:00Z",
            }
        ]
    }
    monkeypatch.setattr("app.adapters.greenhouse.adapter.httpx.get", lambda *args, **kwargs: DummyResponse(greenhouse_payload))

    source = create_source(client, name="Historical Source", base_slug="historical-source")

    run_response = client.post(f"/sources/{source['id']}/run")
    assert run_response.status_code == 200

    jobs_response = client.get("/jobs")
    assert jobs_response.status_code == 200
    job_id = jobs_response.json()[0]["id"]

    tracking_response = client.post(
        f"/jobs/{job_id}/tracking-status",
        json={"tracking_status": "saved", "note_text": "Keep for history"},
    )
    assert tracking_response.status_code == 200

    delete_page = client.get(f"/sources/{source['id']}/delete", headers={"accept": "text/html"})
    assert delete_page.status_code == 200
    assert "Historical Source" in delete_page.text
    assert "existing history" in delete_page.text
    assert "historical source reference" in delete_page.text
    assert "Tracked jobs" in delete_page.text

    delete_response = client.post(
        f"/sources/{source['id']}/delete",
        headers={"content-type": "application/x-www-form-urlencoded", "accept": "text/html"},
        data={},
        follow_redirects=False,
    )
    assert delete_response.status_code == 303

    historical_job_page = client.get(f"/jobs/{job_id}", headers={"accept": "text/html"})
    assert historical_job_page.status_code == 200
    assert "Historical Safety Engineer" in historical_job_page.text
    assert "Historical Source" in historical_job_page.text

    historical_job_api = client.get(f"/jobs/{job_id}")
    assert historical_job_api.status_code == 200
    assert historical_job_api.json()["source_links"][0]["source_id"] == source["id"]
