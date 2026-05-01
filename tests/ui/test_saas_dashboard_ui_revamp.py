import re

from app.persistence.models import JobPosting, Source, utcnow


HTML_HEADERS = {"accept": "text/html"}


def seed_tracked_job(session) -> JobPosting:
    now = utcnow()
    source = seed_source(session)
    job = JobPosting(
        canonical_key="ui-shell:tracked-job",
        primary_source_id=source.id,
        title="UI Shell Backend Engineer",
        company_name="Shell Co",
        job_url="https://example.com/ui-shell-job",
        normalized_job_url="https://example.com/ui-shell-job",
        location_text="Remote",
        description_text="Tracked job for UI shell detail coverage.",
        current_state="active",
        latest_bucket="matched",
        latest_score=88,
        tracking_status="saved",
        first_seen_at=now,
        last_seen_at=now,
        last_ingested_at=now,
    )
    session.add(job)
    session.commit()
    session.refresh(job)
    return job


def seed_source(session) -> Source:
    source = Source(
        name="UI Shell Source",
        source_type="greenhouse",
        base_url="https://boards.greenhouse.io/ui-shell-source",
        external_identifier="ui-shell-source",
        company_name="Shell Co",
        dedupe_key="greenhouse||ui-shell-source",
        is_active=True,
    )
    session.add(source)
    session.commit()
    session.refresh(source)
    return source


def _assert_html_shell(response, expected_page_key: str, expected_title: str) -> None:
    assert response.status_code == 200, response.text[:500]
    assert response.headers["content-type"].startswith("text/html"), response.text[:500]
    body = response.text
    assert '<div class="app-shell"' in body
    assert f'data-page-key="{expected_page_key}"' in body
    assert expected_title in body
    assert 'href="http://testserver/static/css/app.css"' in body
    assert 'src="http://testserver/static/js/app.js"' in body


def test_dashboard_renders_html_shell(client) -> None:
    response = client.get("/dashboard", headers=HTML_HEADERS)
    _assert_html_shell(response, "dashboard", "Operational dashboard")


def test_jobs_index_renders_management_table_ui(client) -> None:
    response = client.get("/jobs", headers=HTML_HEADERS)
    _assert_html_shell(response, "jobs", "Job pipeline")
    assert 'Apply filters' in response.text
    assert 'Search title, company, or description' in response.text


def test_job_detail_renders_html_detail_view(client, session) -> None:
    job_id = seed_tracked_job(session).id
    response = client.get(f"/jobs/{job_id}", headers=HTML_HEADERS)
    _assert_html_shell(response, "jobs", "Update tracking")


def test_sources_index_renders_management_table_ui(client) -> None:
    response = client.get("/sources", headers=HTML_HEADERS)
    _assert_html_shell(response, "sources", "Source inventory")
    assert 'Add source' in response.text
    assert 'Import CSV' in response.text


def test_source_detail_renders_html_detail_view(client, session) -> None:
    seed_source(session)
    source_index = client.get("/sources", headers=HTML_HEADERS)
    match = re.search(r'/sources/(\d+)"', source_index.text)
    assert match, source_index.text[:1000]
    source_id = match.group(1)
    response = client.get(f"/sources/{source_id}", headers=HTML_HEADERS)
    _assert_html_shell(response, "sources", "Recent runs")


def test_source_create_validation_uses_html_error_state(client) -> None:
    response = client.post(
        "/sources",
        data={"name": "", "source_type": "greenhouse", "base_url": ""},
        headers=HTML_HEADERS,
    )
    assert response.status_code == 400
    assert response.headers["content-type"].startswith("text/html")
    assert 'Source update failed.' in response.text


def test_source_health_renders_in_shared_shell(client) -> None:
    response = client.get("/source-health", headers=HTML_HEADERS)
    _assert_html_shell(response, "source_health", "Source health")
    assert 'Review source readiness' in response.text


def test_tracking_page_renders_in_shared_shell(client) -> None:
    response = client.get("/tracking", headers=HTML_HEADERS)
    _assert_html_shell(response, "tracking", "Tracked jobs")
