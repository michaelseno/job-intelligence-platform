from __future__ import annotations

from app.domain.job_preferences import get_default_job_filter_preferences
from app.persistence.models import Source, SourceRun


def add_source(session, name: str, *, health_state: str = "healthy", is_active: bool = True) -> Source:
    source = Source(
        name=name,
        source_type="greenhouse",
        base_url=f"https://boards.greenhouse.io/{name.lower()}",
        external_identifier=name.lower(),
        dedupe_key=f"greenhouse||{name}",
        health_state=health_state,
        is_active=is_active,
    )
    session.add(source)
    session.commit()
    session.refresh(source)
    return source


def test_preview_selected_contract_dedupes_and_reports_skips(client, session):
    healthy = add_source(session, "healthy")
    warning = add_source(session, "warning", health_state="warning")

    response = client.post(
        "/sources/batch-runs/preview",
        json={"mode": "selected", "source_ids": [healthy.id, warning.id, healthy.id, 99999]},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["mode"] == "selected"
    assert data["eligible_count"] == 1
    assert [source["source_id"] for source in data["eligible_sources"]] == [healthy.id]
    assert [source["source_id"] for source in data["skipped_sources"]] == [warning.id, 99999]


def test_preview_selected_requires_source_ids(client):
    response = client.post("/sources/batch-runs/preview", json={"mode": "selected"})

    assert response.status_code == 422


def test_start_zero_eligible_returns_completed_and_status_summary(client, session):
    add_source(session, "warning", health_state="warning")
    preview_response = client.post("/sources/batch-runs/preview", json={"mode": "all"})
    assert preview_response.status_code == 200

    start_response = client.post(
        "/sources/batch-runs",
        json={"preview_id": preview_response.json()["preview_id"], "job_preferences": get_default_job_filter_preferences().model_dump()},
    )

    assert start_response.status_code == 200
    start_data = start_response.json()
    assert start_data["status"] == "completed"

    status_response = client.get(start_data["poll_url"])
    assert status_response.status_code == 200
    status_data = status_response.json()
    assert status_data["eligible_count"] == 0
    assert status_data["skipped_count"] == 1
    assert status_data["source_results"] == []
    assert session.query(SourceRun).count() == 0


def test_start_consumes_preview_and_rejects_duplicate_start(client, session):
    add_source(session, "warning", health_state="warning")
    preview_response = client.post("/sources/batch-runs/preview", json={"mode": "all"})
    preview_id = preview_response.json()["preview_id"]
    payload = {"preview_id": preview_id, "job_preferences": get_default_job_filter_preferences().model_dump()}

    assert client.post("/sources/batch-runs", json=payload).status_code == 200
    duplicate_response = client.post("/sources/batch-runs", json=payload)

    assert duplicate_response.status_code == 404
