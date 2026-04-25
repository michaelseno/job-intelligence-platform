from __future__ import annotations

from app.persistence.models import JobPosting, Source, SourceRun


def test_delete_source_response_queues_cleanup(client, monkeypatch):
    queued: list[int] = []
    monkeypatch.setattr("app.web.routes.run_source_delete_cleanup", lambda source_id: queued.append(source_id))
    create_response = client.post(
        "/sources",
        json={
            "name": "Cleanup API Source",
            "source_type": "greenhouse",
            "base_url": "https://boards.greenhouse.io/cleanup-api",
            "external_identifier": "cleanup-api",
        },
    )
    assert create_response.status_code == 201
    source_id = create_response.json()["id"]

    delete_response = client.delete(f"/sources/{source_id}")

    assert delete_response.status_code == 200
    payload = delete_response.json()
    assert payload["deleted"] is True
    assert payload["source_id"] == source_id
    assert payload["cleanup_queued"] is True
    assert payload["cleanup_status"] == "queued"
    assert queued == [source_id]


def test_jobs_api_and_detail_hide_pending_cleanup_non_retained_jobs(client, session):
    source = Source(name="Deleted", source_type="greenhouse", base_url="https://boards.greenhouse.io/deleted-api", external_identifier="deleted-api", dedupe_key="deleted-api", is_active=False)
    session.add(source)
    session.commit()
    run = SourceRun(source_id=source.id, trigger_type="manual", status="success")
    session.add(run)
    session.commit()
    retained = JobPosting(canonical_key="api-retained", primary_source_id=source.id, title="API Retained", job_url="https://example.com/api-retained", latest_bucket="matched", current_state="active")
    hidden = JobPosting(canonical_key="api-hidden", primary_source_id=source.id, title="API Hidden", job_url="https://example.com/api-hidden", latest_bucket="review", current_state="active")
    session.add_all([retained, hidden])
    session.commit()
    source.deleted_at = source.created_at
    session.add(source)
    session.commit()

    jobs_response = client.get("/jobs")

    assert jobs_response.status_code == 200
    assert [job["id"] for job in jobs_response.json()] == [retained.id]
    assert client.get(f"/jobs/{hidden.id}").status_code == 404
    assert client.get(f"/jobs/{retained.id}").status_code == 200
